"""Contract: retrieving a source vacancy by its ref."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.support.builders import DEFAULT_REF, make_source_vacancy

from vacancy_aggregator.core.models import SourceRef, Title

if TYPE_CHECKING:
    from vacancy_aggregator.core.ports import VacancyRepository


async def test_returns_the_stored_vacancy(repository: VacancyRepository) -> None:
    source = make_source_vacancy()
    await repository.save_source_vacancy(source)
    assert await repository.find_source_vacancy(source.ref) == source


async def test_returns_none_for_unknown_ref(repository: VacancyRepository) -> None:
    assert await repository.find_source_vacancy(SourceRef("hh", "missing")) is None


async def test_distinguishes_sources_with_same_source_id(
    repository: VacancyRepository,
) -> None:
    hh = make_source_vacancy(ref=SourceRef("hh", "1"))
    habr = make_source_vacancy(ref=SourceRef("habr", "1"))
    await repository.save_source_vacancy(hh)
    await repository.save_source_vacancy(habr)
    assert await repository.find_source_vacancy(hh.ref) == hh
    assert await repository.find_source_vacancy(habr.ref) == habr


async def test_returns_latest_saved_state(repository: VacancyRepository) -> None:
    await repository.save_source_vacancy(make_source_vacancy())
    updated = make_source_vacancy(title=Title("senior python developer"))
    await repository.save_source_vacancy(updated)
    assert await repository.find_source_vacancy(DEFAULT_REF) == updated
