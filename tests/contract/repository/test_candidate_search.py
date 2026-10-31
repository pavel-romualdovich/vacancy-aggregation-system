"""Contract: searching domain candidates by the dedup lookup key."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from tests.contract.repository.conftest import DEFAULT_KEY
from tests.support.builders import (
    PUBLISHED_AT,
    make_domain_vacancy,
    make_source_vacancy,
)

from vacancy_aggregator.core.models import DomainVacancy, Employer, Region, Title
from vacancy_aggregator.core.services.deduplicator import candidate_key, is_duplicate

if TYPE_CHECKING:
    from vacancy_aggregator.core.ports import VacancyRepository

OTHER_TITLE = make_domain_vacancy(title=Title("java developer"))
OTHER_EMPLOYER = make_domain_vacancy(employer=Employer("other"))
OTHER_REGION = make_domain_vacancy(region=Region("saint petersburg"))
NO_REGION = make_domain_vacancy(region=None)


@pytest.mark.parametrize(
    ("stored", "expected_indexes"),
    [
        pytest.param([], [], id="empty-repository"),
        pytest.param([OTHER_TITLE], [], id="different-title"),
        pytest.param([OTHER_EMPLOYER], [], id="different-employer"),
        pytest.param([OTHER_REGION], [], id="different-region"),
        pytest.param([NO_REGION], [], id="missing-region"),
        pytest.param([OTHER_TITLE, OTHER_EMPLOYER, OTHER_REGION], [], id="none-match"),
        pytest.param(
            [OTHER_TITLE, make_domain_vacancy(), OTHER_REGION],
            [1],
            id="single-match",
        ),
        pytest.param(
            [OTHER_TITLE, make_domain_vacancy(), OTHER_EMPLOYER],
            [1],
            id="single-match-among-others",
        ),
        pytest.param(
            [
                OTHER_TITLE,
                make_domain_vacancy(published_at=PUBLISHED_AT),
                make_domain_vacancy(published_at=PUBLISHED_AT - timedelta(days=400)),
                OTHER_REGION,
            ],
            [1, 2],
            id="multiple-matches",
        ),
    ],
)
async def test_returns_only_full_key_matches(
    repository: VacancyRepository,
    stored: list[DomainVacancy],
    expected_indexes: list[int],
) -> None:
    """A vacancy matching only part of the key is not returned."""
    for domain in stored:
        await repository.save_domain_vacancy(domain)
    found = list(await repository.find_domain_candidates(DEFAULT_KEY))
    assert found == [stored[index] for index in expected_indexes]


async def test_ignores_dedup_window(repository: VacancyRepository) -> None:
    """The index is a superset: only is_duplicate narrows by the window."""
    recent = make_domain_vacancy()
    old = make_domain_vacancy(published_at=PUBLISHED_AT - timedelta(days=400))
    await repository.save_domain_vacancy(recent)
    await repository.save_domain_vacancy(old)
    assert list(await repository.find_domain_candidates(DEFAULT_KEY)) == [
        recent,
        old,
    ]


async def test_never_loses_a_duplicate(repository: VacancyRepository) -> None:
    existing = make_domain_vacancy()
    await repository.save_domain_vacancy(existing)
    candidate = make_source_vacancy()
    key = candidate_key(candidate)
    assert key is not None
    assert is_duplicate(candidate, existing) is True
    assert existing in await repository.find_domain_candidates(key)
