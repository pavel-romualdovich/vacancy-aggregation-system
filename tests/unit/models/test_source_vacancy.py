"""Tests for the SourceVacancy entity invariants."""

from __future__ import annotations

from datetime import timedelta

import pytest
from tests.support.builders import (
    LAST_SEEN_AT,
    make_source_vacancy,
)

from vacancy_aggregator.core.models import Skills, uuid7


def test_rejects_detected_updated_after_last_seen() -> None:
    with pytest.raises(ValueError, match="detected_updated_at"):
        make_source_vacancy(
            last_seen_at=LAST_SEEN_AT,
            detected_updated_at=LAST_SEEN_AT + timedelta(days=1),
        )


def test_accepts_detected_updated_at_last_seen() -> None:
    vacancy = make_source_vacancy(detected_updated_at=LAST_SEEN_AT)
    assert vacancy.detected_updated_at == LAST_SEEN_AT


def test_rejects_empty_description() -> None:
    with pytest.raises(ValueError, match="description"):
        make_source_vacancy(description="")


def test_accepts_none_description_and_region() -> None:
    vacancy = make_source_vacancy(description=None, region=None)
    assert vacancy.description is None
    assert vacancy.region is None


def test_accepts_normalized_skills() -> None:
    vacancy = make_source_vacancy(skills=Skills(["python", "django"]))
    assert vacancy.skills == frozenset({"python", "django"})


def test_domain_id_defaults_to_none() -> None:
    assert make_source_vacancy().domain_id is None


def test_domain_id_is_settable() -> None:
    domain_id = uuid7()
    assert make_source_vacancy(domain_id=domain_id).domain_id == domain_id
