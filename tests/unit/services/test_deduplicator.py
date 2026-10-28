"""Tests for the vacancy deduplication rule."""

from __future__ import annotations

from datetime import datetime, timedelta

from vacancy_aggregator.core.models import (
    DomainVacancy,
    SourceRef,
    SourceVacancy,
)
from vacancy_aggregator.core.services.deduplicator import is_duplicate

PUBLISHED_AT = datetime(2026, 1, 1, 12, 0)
WINDOW = timedelta(days=30)


def make_source_vacancy(
    *,
    title: str = "Python Developer",
    published_at: datetime = PUBLISHED_AT,
    employer: str = "Acme",
    region: str | None = "Moscow",
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
    title: str = "Python Developer",
    published_at: datetime = PUBLISHED_AT,
    employer: str = "Acme",
    region: str | None = "Moscow",
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
    candidate = make_source_vacancy(title="Java Developer")
    existing = make_domain_vacancy()
    assert is_duplicate(candidate, existing, window=WINDOW) is False


def test_not_duplicate_when_region_differs() -> None:
    candidate = make_source_vacancy(region="Saint Petersburg")
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
    candidate = make_source_vacancy(employer="Other")
    existing = make_domain_vacancy()
    assert is_duplicate(candidate, existing, window=WINDOW) is False
