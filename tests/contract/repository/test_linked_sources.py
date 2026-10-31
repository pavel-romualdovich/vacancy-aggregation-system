"""Contract: listing source vacancies linked to a domain vacancy."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from tests.contract.conftest import make_source_vacancy

from vacancy_aggregator.core.models import SourceRef, uuid7

if TYPE_CHECKING:
    from vacancy_aggregator.core.ports import VacancyRepository


@pytest.mark.parametrize(
    ("linked_count", "has_unrelated"),
    [
        pytest.param(0, False, id="no-linked-sources"),
        pytest.param(1, False, id="single-linked-source"),
        pytest.param(3, False, id="multiple-linked-sources"),
        pytest.param(2, True, id="linked-with-unrelated"),
    ],
)
async def test_returns_exactly_linked_sources(
    repository: VacancyRepository,
    linked_count: int,
    *,
    has_unrelated: bool,
) -> None:
    """Sources of other domains and unlinked sources are not returned."""
    domain_id = uuid7()
    linked = [
        make_source_vacancy(ref=SourceRef("hh", str(index)), domain_id=domain_id)
        for index in range(linked_count)
    ]
    unrelated = [
        make_source_vacancy(ref=SourceRef("habr", "1"), domain_id=uuid7()),
        make_source_vacancy(ref=SourceRef("habr", "2"), domain_id=None),
    ]
    for source in linked + (unrelated if has_unrelated else []):
        await repository.save_source_vacancy(source)

    found = list(await repository.find_sources_of(domain_id))
    assert len(found) == linked_count
    assert {source.ref for source in found} == {source.ref for source in linked}


async def test_returns_empty_for_unknown_domain(
    repository: VacancyRepository,
) -> None:
    assert list(await repository.find_sources_of(uuid7())) == []
