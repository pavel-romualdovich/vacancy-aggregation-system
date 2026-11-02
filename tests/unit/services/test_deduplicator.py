"""Tests for the vacancy deduplication rule."""

from __future__ import annotations

from datetime import timedelta

from tests.support.builders import (
    DEFAULT_EMPLOYER,
    DEFAULT_REGION,
    DEFAULT_TITLE,
    PUBLISHED_AT,
    make_domain_vacancy,
    make_source_vacancy,
)

from vacancy_aggregator.core.models import CandidateKey, Employer, Region, Title
from vacancy_aggregator.core.services.deduplicator import candidate_key, is_duplicate

WINDOW = timedelta(days=30)


def test_duplicate_when_all_conditions_met() -> None:
    assert is_duplicate(make_source_vacancy(), make_domain_vacancy(), window=WINDOW)


def test_not_duplicate_when_window_exceeded() -> None:
    candidate = make_source_vacancy(
        published_at=PUBLISHED_AT + WINDOW + timedelta(seconds=1)
    )
    assert not is_duplicate(candidate, make_domain_vacancy(), window=WINDOW)


def test_duplicate_on_exact_window_boundary() -> None:
    candidate = make_source_vacancy(published_at=PUBLISHED_AT + WINDOW)
    assert is_duplicate(candidate, make_domain_vacancy(), window=WINDOW)


def test_window_is_symmetric() -> None:
    candidate = make_source_vacancy(published_at=PUBLISHED_AT - WINDOW)
    assert is_duplicate(candidate, make_domain_vacancy(), window=WINDOW)


def test_not_duplicate_when_title_differs() -> None:
    candidate = make_source_vacancy(title=Title("java developer"))
    assert not is_duplicate(candidate, make_domain_vacancy(), window=WINDOW)


def test_not_duplicate_when_region_differs() -> None:
    candidate = make_source_vacancy(region=Region("saint petersburg"))
    assert not is_duplicate(candidate, make_domain_vacancy(), window=WINDOW)


def test_region_required_in_both() -> None:
    candidate_missing = make_source_vacancy(region=None)
    existing_filled = make_domain_vacancy()
    assert not is_duplicate(candidate_missing, existing_filled, window=WINDOW)

    candidate_filled = make_source_vacancy()
    existing_missing = make_domain_vacancy(region=None)
    assert not is_duplicate(candidate_filled, existing_missing, window=WINDOW)


def test_not_duplicate_when_employer_differs() -> None:
    candidate = make_source_vacancy(employer=Employer("other"))
    assert not is_duplicate(candidate, make_domain_vacancy(), window=WINDOW)


def test_candidate_key_reflects_the_rule() -> None:
    key = candidate_key(make_source_vacancy())
    assert key == CandidateKey(
        employer=DEFAULT_EMPLOYER,
        title=DEFAULT_TITLE,
        region=DEFAULT_REGION,
    )


def test_candidate_key_is_none_without_region() -> None:
    assert candidate_key(make_source_vacancy(region=None)) is None


def test_candidate_key_matches_duplicate_candidates() -> None:
    """The index must never lose a duplicate: every matching pair shares a key."""
    candidate = make_source_vacancy()
    existing = make_domain_vacancy()
    assert is_duplicate(candidate, existing, window=WINDOW)

    key = candidate_key(candidate)
    assert key is not None
    assert (key.employer, key.title, key.region) == (
        existing.business_fields.employer,
        existing.business_fields.title,
        existing.business_fields.region,
    )
