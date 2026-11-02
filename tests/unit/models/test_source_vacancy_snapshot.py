"""Tests for the SourceVacancySnapshot model invariants."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta
from typing import Any, cast

import pytest

from vacancy_aggregator.core.models import (
    Currency,
    Employer,
    EmploymentType,
    Experience,
    Grade,
    Region,
    Salary,
    Skills,
    SourceRef,
    SourceVacancySnapshot,
    Specialization,
    Title,
    VacancyBusinessFields,
    WorkFormat,
)

PUBLISHED_AT = datetime(2026, 1, 1, 12, 0)
COLLECTED_AT = PUBLISHED_AT + timedelta(days=1)
REF = SourceRef(source="hh", source_id="1")
TITLE = Title("python developer")
EMPLOYER = Employer("acme")


def test_accepts_canonical_values() -> None:
    snapshot = SourceVacancySnapshot(
        ref=REF,
        business_fields=VacancyBusinessFields(
            title=TITLE,
            employer=EMPLOYER,
            description="write clean code",
            salary=Salary(
                from_amount=100,
                to_amount=200,
                currency=Currency.RUB,
                gross=False,
            ),
            region=Region("moscow"),
            experience=Experience.FROM_1_TO_3,
            employment_type=EmploymentType.FULL_TIME,
            work_format=WorkFormat.REMOTE,
            grade=Grade.MIDDLE,
            specialization=Specialization.BACKEND,
            skills=Skills(["python", "django"]),
        ),
        collected_at=COLLECTED_AT,
        published_at=PUBLISHED_AT,
        is_active=True,
    )
    assert snapshot.ref == REF
    assert snapshot.published_at == PUBLISHED_AT
    assert snapshot.collected_at == COLLECTED_AT
    assert snapshot.business_fields.title == TITLE
    assert snapshot.business_fields.employer == EMPLOYER
    assert snapshot.business_fields.description == "write clean code"
    assert snapshot.business_fields.salary == Salary(100, 200, Currency.RUB, False)
    assert snapshot.business_fields.region == Region("moscow")
    assert snapshot.business_fields.experience == Experience.FROM_1_TO_3
    assert snapshot.business_fields.employment_type == EmploymentType.FULL_TIME
    assert snapshot.business_fields.work_format == WorkFormat.REMOTE
    assert snapshot.business_fields.grade == Grade.MIDDLE
    assert snapshot.business_fields.specialization == Specialization.BACKEND
    assert snapshot.business_fields.skills == Skills(["python", "django"])
    assert snapshot.is_active is True


def test_rejects_empty_description() -> None:
    with pytest.raises(ValueError, match="description"):
        SourceVacancySnapshot(
            ref=REF,
            business_fields=VacancyBusinessFields(
                title=TITLE,
                employer=EMPLOYER,
                description="",
            ),
            collected_at=COLLECTED_AT,
            published_at=PUBLISHED_AT,
        )


def test_rejects_blank_description() -> None:
    with pytest.raises(ValueError, match="description"):
        SourceVacancySnapshot(
            ref=REF,
            business_fields=VacancyBusinessFields(
                title=TITLE,
                employer=EMPLOYER,
                description="   ",
            ),
            collected_at=COLLECTED_AT,
            published_at=PUBLISHED_AT,
        )


def test_accepts_none_optional_fields() -> None:
    snapshot = SourceVacancySnapshot(
        ref=REF,
        business_fields=VacancyBusinessFields(
            title=TITLE,
            employer=EMPLOYER,
            description=None,
            salary=None,
            region=None,
            experience=None,
            employment_type=None,
            work_format=None,
            grade=None,
            specialization=None,
        ),
        collected_at=COLLECTED_AT,
        published_at=PUBLISHED_AT,
    )
    assert snapshot.business_fields.description is None
    assert snapshot.business_fields.salary is None
    assert snapshot.business_fields.region is None
    assert snapshot.business_fields.experience is None
    assert snapshot.business_fields.employment_type is None
    assert snapshot.business_fields.work_format is None
    assert snapshot.business_fields.grade is None
    assert snapshot.business_fields.specialization is None
    assert snapshot.is_active is None


def test_defaults() -> None:
    snapshot = SourceVacancySnapshot(
        ref=REF,
        business_fields=VacancyBusinessFields(title=TITLE, employer=EMPLOYER),
        collected_at=COLLECTED_AT,
    )
    assert snapshot.published_at is None
    assert snapshot.is_active is None
    assert snapshot.business_fields.description is None
    assert snapshot.business_fields.salary is None
    assert snapshot.business_fields.region is None
    assert snapshot.business_fields.skills == Skills()


def test_is_frozen() -> None:
    snapshot = SourceVacancySnapshot(
        ref=REF,
        business_fields=VacancyBusinessFields(title=TITLE, employer=EMPLOYER),
        collected_at=COLLECTED_AT,
        published_at=PUBLISHED_AT,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        cast("Any", snapshot).business_fields = VacancyBusinessFields(
            title=Title("other"), employer=EMPLOYER
        )
