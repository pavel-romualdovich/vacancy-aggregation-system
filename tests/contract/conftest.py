"""Shared builders for the contract suites of all ports."""

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

PUBLISHED_AT = datetime(2026, 1, 1, 12, 0)
DEFAULT_REF = SourceRef(source="hh", source_id="1")
DEFAULT_TITLE = Title("python developer")
DEFAULT_EMPLOYER = Employer("acme")
DEFAULT_REGION = Region("moscow")


def make_source_vacancy(
    *,
    ref: SourceRef = DEFAULT_REF,
    title: Title = DEFAULT_TITLE,
    published_at: datetime = PUBLISHED_AT,
    employer: Employer = DEFAULT_EMPLOYER,
    region: Region | None = DEFAULT_REGION,
    domain_id: UUID | None = None,
) -> SourceVacancy:
    """Build a SourceVacancy with convenient defaults."""
    return SourceVacancy(
        ref=ref,
        title=title,
        published_at=published_at,
        last_seen_at=published_at + timedelta(days=1),
        employer=employer,
        region=region,
        domain_id=domain_id,
    )


def make_domain_vacancy(
    *,
    title: Title = DEFAULT_TITLE,
    published_at: datetime = PUBLISHED_AT,
    employer: Employer = DEFAULT_EMPLOYER,
    region: Region | None = DEFAULT_REGION,
    domain_id: UUID | None = None,
    description: str | None = None,
) -> DomainVacancy:
    """Build a DomainVacancy with convenient defaults."""
    return DomainVacancy(
        title=title,
        published_at=published_at,
        employer=employer,
        region=region,
        id=domain_id or uuid7(),
        description=description,
    )
