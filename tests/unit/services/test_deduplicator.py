"""Tests for the vacancy deduplication rule."""

from __future__ import annotations

from datetime import datetime, timedelta

from vacancy_aggregator.core.models import (
    DomainVacancy,
    Employer,
    Region,
    SourceRef,
    SourceVacancy,
    Title,
)
from vacancy_aggregator.core.services.deduplicator import is_duplicate

PUBLISHED_AT = datetime(2026, 1, 1, 12, 0)
WINDOW = timedelta(days=30)
DEFAULT_TITLE = Title("python developer")
DEFAULT_EMPLOYER = Employer("acme")
DEFAULT_REGION = Region("moscow")


def make_source_vacancy(
    *,
    title: Title = DEFAULT_TITLE,
    published_at: datetime = PUBLISHED_AT,
    employer: Employer = DEFAULT_EMPLOYER,
    region: Region | None = DEFAULT_REGION,
) -> SourceVacancy:
    """Build a SourceVacancy with convenient defaults."""
    return SourceVacancy(
        ref=SourceRef(source="hh", source_id="1"),
        title=title,
        published_at=published_at,
        last_seen_at=published_at + timedelta(days=1),
        employer=employer,
        region=region,
    )


def make_domain_vacancy(
    *,
    title: Title = DEFAULT_TITLE,
    published_at: datetime = PUBLISHED_AT,
    employer: Employer = DEFAULT_EMPLOYER,
    region: Region | None = DEFAULT_REGION,
) -> DomainVacancy:
    """Build a DomainVacancy with convenient defaults."""
    return DomainVacancy(
        title=title,
        published_at=published_at,
        employer=employer,
        region=region,
    )


def test_duplicate_when_all_conditions_met() -> None:
    candidate = make_source_vacancy()
    existing = make_domain_vacancy()
    assert is_duplicate(candidate, existing, window=WINDOW) is True


def test_not_duplicate_when_window_exceeded() -> None:
    candidate = make_source_vacancy(
        published_at=PUBLISHED_AT + WINDOW + timedelta(seconds=1)
    )
    existing = make_domain_vacancy()
    assert is_duplicate(candidate, existing, window=WINDOW) is False


def test_duplicate_on_exact_window_boundary() -> None:
    candidate = make_source_vacancy(published_at=PUBLISHED_AT + WINDOW)
    existing = make_domain_vacancy()
    assert is_duplicate(candidate, existing, window=WINDOW) is True


def test_window_is_symmetric() -> None:
    candidate = make_source_vacancy(published_at=PUBLISHED_AT - WINDOW)
    existing = make_domain_vacancy()
    assert is_duplicate(candidate, existing, window=WINDOW) is True


def test_not_duplicate_when_title_differs() -> None:
    candidate = make_source_vacancy(title=Title("java developer"))
    existing = make_domain_vacancy()
    assert is_duplicate(candidate, existing, window=WINDOW) is False


def test_not_duplicate_when_region_differs() -> None:
    candidate = make_source_vacancy(region=Region("saint petersburg"))
    existing = make_domain_vacancy()
    assert is_duplicate(candidate, existing, window=WINDOW) is False


def test_region_required_in_both() -> None:
    candidate_missing = make_source_vacancy(region=None)
    existing_filled = make_domain_vacancy()
    assert is_duplicate(candidate_missing, existing_filled, window=WINDOW) is False

    candidate_filled = make_source_vacancy()
    existing_missing = make_domain_vacancy(region=None)
    assert is_duplicate(candidate_filled, existing_missing, window=WINDOW) is False


def test_not_duplicate_when_employer_differs() -> None:
    candidate = make_source_vacancy(employer=Employer("other"))
    existing = make_domain_vacancy()
    assert is_duplicate(candidate, existing, window=WINDOW) is False
