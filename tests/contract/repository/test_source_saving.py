"""Contract: persisting a source vacancy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.contract.conftest import DEFAULT_REF, make_source_vacancy

from vacancy_aggregator.core.models import Title

if TYPE_CHECKING:
    from vacancy_aggregator.core.ports import VacancyRepository


async def test_creates_new_vacancy_as_given(
    repository: VacancyRepository,
) -> None:
    source = make_source_vacancy()
    await repository.save_source_vacancy(source)
    assert await repository.find_source_vacancy(DEFAULT_REF) == source


async def test_updates_existing_vacancy_by_ref(
    repository: VacancyRepository,
) -> None:
    await repository.save_source_vacancy(make_source_vacancy())
    updated = make_source_vacancy(title=Title("senior python developer"))
    await repository.save_source_vacancy(updated)
    assert await repository.find_source_vacancy(DEFAULT_REF) == updated


async def test_saving_same_vacancy_twice_keeps_it_unchanged(
    repository: VacancyRepository,
) -> None:
    source = make_source_vacancy()
    await repository.save_source_vacancy(source)
    await repository.save_source_vacancy(source)
    assert await repository.find_source_vacancy(DEFAULT_REF) == source
