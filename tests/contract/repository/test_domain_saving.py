"""Contract: persisting a domain vacancy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.contract.conftest import make_domain_vacancy
from tests.contract.repository.conftest import DEFAULT_KEY

if TYPE_CHECKING:
    from vacancy_aggregator.core.ports import VacancyRepository


async def test_creates_new_vacancy_as_given(
    repository: VacancyRepository,
) -> None:
    domain = make_domain_vacancy()
    await repository.save_domain_vacancy(domain)
    assert list(await repository.find_domain_candidates(DEFAULT_KEY)) == [domain]


async def test_updates_existing_vacancy_by_id(
    repository: VacancyRepository,
) -> None:
    domain = make_domain_vacancy()
    await repository.save_domain_vacancy(domain)
    updated = make_domain_vacancy(domain_id=domain.id, description="python backend")
    await repository.save_domain_vacancy(updated)
    assert list(await repository.find_domain_candidates(DEFAULT_KEY)) == [updated]


async def test_saving_same_vacancy_twice_keeps_it_unchanged(
    repository: VacancyRepository,
) -> None:
    domain = make_domain_vacancy()
    await repository.save_domain_vacancy(domain)
    await repository.save_domain_vacancy(domain)
    assert list(await repository.find_domain_candidates(DEFAULT_KEY)) == [domain]
