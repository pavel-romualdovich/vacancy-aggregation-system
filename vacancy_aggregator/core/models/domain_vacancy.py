"""DomainVacancy — the single aggregated vacancy entity exposed to the API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from uuid6 import uuid7

from vacancy_aggregator.core.models.values import Skills

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from vacancy_aggregator.core.models.enums import (
        EmploymentType,
        Experience,
        Grade,
        Specialization,
        WorkFormat,
    )
    from vacancy_aggregator.core.models.values import Salary


@dataclass(kw_only=True)
class DomainVacancy:
    """One vacancy merged from all of its :class:`SourceVacancy` instances.

    Business fields are the result of the merge rules (freshness via
    ``detected_updated_at`` falling back to ``published_at``; an empty value
    never overwrites a filled one). No technical fields (source, source_id,
    url, service dates) live here, so they cannot leak into the API.

    ``published_at`` is used for ordering and equals the maximum publication
    time across the linked source vacancies. The vacancy is active while at
    least one of its source vacancies is active; ``inactive_since`` is set
    exactly when the vacancy is inactive.
    """

    title: str
    published_at: datetime
    employer: str
    id: UUID = field(default_factory=uuid7)
    description: str | None = None
    salary: Salary | None = None
    region: str | None = None
    experience: Experience | None = None
    employment_type: EmploymentType | None = None
    work_format: WorkFormat | None = None
    grade: Grade | None = None
    specialization: Specialization | None = None
    skills: Skills = field(default_factory=Skills)
    inactive_since: datetime | None = None

    @property
    def is_active(self) -> bool:
        """Whether the vacancy is currently active."""
        return self.inactive_since is None

    def __post_init__(self) -> None:
        """Validate non-empty fields."""
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
