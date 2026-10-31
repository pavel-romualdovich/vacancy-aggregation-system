"""Canonical builders for domain models, shared by every test layer."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from vacancy_aggregator.core.models import (
    DomainVacancy,
    Employer,
    Region,
    SourceRef,
    SourceVacancy,
    Title,
    uuid7,
)

if TYPE_CHECKING:
    from uuid import UUID

    from vacancy_aggregator.core.models import Salary, Skills

PUBLISHED_AT = datetime(2026, 1, 1, 12, 0)
LAST_SEEN_AT = PUBLISHED_AT + timedelta(days=1)
DEFAULT_TITLE = Title("python developer")
DEFAULT_EMPLOYER = Employer("acme")
DEFAULT_REGION = Region("moscow")
DEFAULT_REF = SourceRef(source="hh", source_id="1")


def make_source_vacancy(
    *,
    ref: SourceRef = DEFAULT_REF,
    title: Title = DEFAULT_TITLE,
    published_at: datetime = PUBLISHED_AT,
    last_seen_at: datetime = LAST_SEEN_AT,
    employer: Employer = DEFAULT_EMPLOYER,
    description: str | None = None,
    salary: Salary | None = None,
    region: Region | None = DEFAULT_REGION,
    skills: Skills | None = None,
    detected_updated_at: datetime | None = None,
    domain_id: UUID | None = None,
) -> SourceVacancy:
    """Build a SourceVacancy with convenient defaults."""
    return SourceVacancy(
        ref=ref,
        title=title,
        published_at=published_at,
        last_seen_at=last_seen_at,
        employer=employer,
        description=description,
        salary=salary,
        region=region,
        skills=skills if skills is not None else _empty_skills(),
        detected_updated_at=detected_updated_at,
        domain_id=domain_id,
    )


def make_domain_vacancy(
    *,
    domain_id: UUID | None = None,
    title: Title = DEFAULT_TITLE,
    published_at: datetime = PUBLISHED_AT,
    employer: Employer = DEFAULT_EMPLOYER,
    description: str | None = None,
    salary: Salary | None = None,
    region: Region | None = DEFAULT_REGION,
    skills: Skills | None = None,
    inactive_since: datetime | None = None,
) -> DomainVacancy:
    """Build a DomainVacancy with convenient defaults."""
    return DomainVacancy(
        id=domain_id if domain_id is not None else uuid7(),
        title=title,
        published_at=published_at,
        employer=employer,
        description=description,
        salary=salary,
        region=region,
        skills=skills if skills is not None else _empty_skills(),
        inactive_since=inactive_since,
    )


def _empty_skills() -> Skills:
    """Return an empty Skills set (import deferred to avoid a cycle)."""
    from vacancy_aggregator.core.models import Skills

    return Skills()
