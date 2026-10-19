"""SourceVacancy — normalized vacancy as seen in a single source."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from vacancy_aggregator.core.models.values import Skills

if TYPE_CHECKING:
    from datetime import datetime

    from vacancy_aggregator.core.models.enums import (
        EmploymentType,
        Experience,
        Grade,
        Specialization,
        WorkFormat,
    )
    from vacancy_aggregator.core.models.values import Salary, SourceRef


@dataclass(kw_only=True)
class SourceVacancy:
    """A vacancy record coming from one specific source.

    Identity is the :class:`SourceRef` — ``(source, source_id)`` is globally
    unique. Business fields follow the unified representation; the service
    dates stay here and never leak into the public API. The public link is not
    stored: the adapter builds it from ``source_id`` on demand.

    ``published_at`` is a snapshot taken on the first sight of the vacancy in
    the aggregator: it is never refreshed by later collections. If the source
    provides no publication date, the collection time is used. ``last_seen_at``
    is the moment of the latest observation and drives the activity logic.
    ``detected_updated_at`` is the moment the aggregator noticed a change in
    business fields and never exceeds ``last_seen_at``.
    """

    ref: SourceRef
    title: str
    published_at: datetime
    last_seen_at: datetime
    employer: str
    description: str | None = None
    salary: Salary | None = None
    region: str | None = None
    experience: Experience | None = None
    employment_type: EmploymentType | None = None
    work_format: WorkFormat | None = None
    grade: Grade | None = None
    specialization: Specialization | None = None
    skills: Skills = field(default_factory=Skills)
    detected_updated_at: datetime | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate non-empty fields and the detected/last_seen ordering."""
        if not self.title.strip():
            msg = "title must not be empty"
            raise ValueError(msg)
        if not self.employer.strip():
            msg = "employer must not be empty"
            raise ValueError(msg)
        if self.description is not None and not self.description.strip():
            msg = "description must not be empty"
            raise ValueError(msg)
        if self.region is not None and not self.region.strip():
            msg = "region must not be empty"
            raise ValueError(msg)
        if (
            self.detected_updated_at is not None
            and self.detected_updated_at > self.last_seen_at
        ):
            msg = "detected_updated_at must not be after last_seen_at"
            raise ValueError(msg)
