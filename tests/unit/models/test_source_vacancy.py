"""Tests for the SourceVacancy entity invariants."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from vacancy_aggregator.core.models import Skills, SourceRef, SourceVacancy

PUBLISHED_AT = datetime(2026, 1, 1, 12, 0)
LAST_SEEN_AT = datetime(2026, 1, 2, 12, 0)
EMPTY_SKILLS = Skills()


def make_source_vacancy(
    title: str = "Python Dev",
    published_at: datetime = PUBLISHED_AT,
    last_seen_at: datetime = LAST_SEEN_AT,
    employer: str = "Acme",
    description: str | None = None,
    region: str | None = None,
    skills: Skills = EMPTY_SKILLS,
    detected_updated_at: datetime | None = None,
) -> SourceVacancy:
    """Build a SourceVacancy with convenient defaults."""
    return SourceVacancy(
        ref=SourceRef(source="hh", source_id="123"),
        title=title,
        published_at=published_at,
        last_seen_at=last_seen_at,
        employer=employer,
        description=description,
        region=region,
        skills=skills,
        detected_updated_at=detected_updated_at,
    )


def test_rejects_detected_updated_after_last_seen() -> None:
    with pytest.raises(ValueError, match="detected_updated_at"):
        make_source_vacancy(detected_updated_at=LAST_SEEN_AT + timedelta(days=1))


def test_accepts_detected_updated_at_last_seen() -> None:
    vacancy = make_source_vacancy(detected_updated_at=LAST_SEEN_AT)
    assert vacancy.detected_updated_at == LAST_SEEN_AT


def test_rejects_empty_title() -> None:
    with pytest.raises(ValueError, match="title"):
        make_source_vacancy(title="")


def test_rejects_blank_employer() -> None:
    with pytest.raises(ValueError, match="employer"):
        make_source_vacancy(employer="   ")


def test_rejects_empty_description() -> None:
    with pytest.raises(ValueError, match="description"):
        make_source_vacancy(description="")


def test_rejects_blank_region() -> None:
    with pytest.raises(ValueError, match="region"):
        make_source_vacancy(region="   ")


def test_accepts_none_description_and_region() -> None:
    vacancy = make_source_vacancy(description=None, region=None)
    assert vacancy.description is None
    assert vacancy.region is None


def test_accepts_normalized_skills() -> None:
    vacancy = make_source_vacancy(skills=Skills(["python", "django"]))
    assert vacancy.skills == frozenset({"python", "django"})
