"""Tests for the DomainVacancy entity invariants."""

from __future__ import annotations

from datetime import datetime

import pytest

from vacancy_aggregator.core.models import DomainVacancy, Skills

PUBLISHED_AT = datetime(2026, 1, 1, 12, 0)
INACTIVE_AT = datetime(2026, 1, 2, 12, 0)


def make_domain_vacancy(
    title: str = "Python Dev",
    published_at: datetime = PUBLISHED_AT,
    employer: str = "Acme",
    inactive_since: datetime | None = None,
) -> DomainVacancy:
    """Build a DomainVacancy with convenient defaults."""
    return DomainVacancy(
        title=title,
        published_at=published_at,
        employer=employer,
        inactive_since=inactive_since,
    )


def test_is_active_when_no_inactive_since() -> None:
    vacancy = make_domain_vacancy()
    assert vacancy.is_active is True


def test_is_inactive_when_inactive_since_set() -> None:
    vacancy = make_domain_vacancy(inactive_since=INACTIVE_AT)
    assert vacancy.is_active is False


def test_rejects_empty_title() -> None:
    with pytest.raises(ValueError, match="title"):
        make_domain_vacancy(title="")


def test_rejects_blank_title() -> None:
    with pytest.raises(ValueError, match="title"):
        make_domain_vacancy(title="   ")


def test_rejects_empty_employer() -> None:
    with pytest.raises(ValueError, match="employer"):
        make_domain_vacancy(employer="")


def test_rejects_empty_description() -> None:
    with pytest.raises(ValueError, match="description"):
        DomainVacancy(
            title="Python Dev",
            published_at=PUBLISHED_AT,
            employer="Acme",
            description="",
        )


def test_rejects_blank_region() -> None:
    with pytest.raises(ValueError, match="region"):
        DomainVacancy(
            title="Python Dev",
            published_at=PUBLISHED_AT,
            employer="Acme",
            region="   ",
        )


def test_accepts_none_optional_fields() -> None:
    vacancy = DomainVacancy(
        title="Python Dev",
        published_at=PUBLISHED_AT,
        employer="Acme",
        description=None,
        region=None,
    )
    assert vacancy.description is None
    assert vacancy.region is None


def test_accepts_normalized_skills() -> None:
    vacancy = DomainVacancy(
        title="Python Dev",
        published_at=PUBLISHED_AT,
        employer="Acme",
        skills=Skills(["python", "django"]),
    )
    assert vacancy.skills == frozenset({"python", "django"})
