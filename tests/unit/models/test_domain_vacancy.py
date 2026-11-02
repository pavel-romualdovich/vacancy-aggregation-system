"""Tests for the DomainVacancy entity invariants."""

from __future__ import annotations

import pytest
from tests.support.builders import PUBLISHED_AT, make_domain_vacancy

from vacancy_aggregator.core.models import (
    DomainVacancy,
    Employer,
    Skills,
    Title,
    VacancyBusinessFields,
)


def test_is_active_when_no_inactive_since() -> None:
    assert make_domain_vacancy().is_active is True


def test_is_inactive_when_inactive_since_set() -> None:
    vacancy = make_domain_vacancy(inactive_since=PUBLISHED_AT)
    assert vacancy.is_active is False


def test_rejects_empty_description() -> None:
    with pytest.raises(ValueError, match="description"):
        make_domain_vacancy(description="")


def test_accepts_none_optional_fields() -> None:
    vacancy = DomainVacancy(
        business_fields=VacancyBusinessFields(
            title=Title("python developer"),
            employer=Employer("acme"),
            description=None,
            region=None,
        ),
        published_at=PUBLISHED_AT,
    )
    assert vacancy.business_fields.description is None
    assert vacancy.business_fields.region is None


def test_accepts_normalized_skills() -> None:
    vacancy = make_domain_vacancy(skills=Skills(["python", "django"]))
    assert vacancy.business_fields.skills == frozenset({"python", "django"})
