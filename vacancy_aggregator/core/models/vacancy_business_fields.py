"""Value object with the business fields shared by every vacancy model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from vacancy_aggregator.core.models.values import Employer, Region, Skills, Title

if TYPE_CHECKING:
    from vacancy_aggregator.core.models.enums import (
        EmploymentType,
        Experience,
        Grade,
        Specialization,
        WorkFormat,
    )
    from vacancy_aggregator.core.models.values import Salary


@dataclass(frozen=True, kw_only=True)
class VacancyBusinessFields:
    """Value object of the unified vacancy business fields.

    One source of truth for the unified vacancy representation: the
    :class:`SourceVacancySnapshot` carries them from the source, the
    :class:`SourceVacancy` record persists them, the :class:`DomainVacancy`
    merges them. Models *contain* this value object instead of inheriting
    from it, so the frozen status stays a property of each container — the
    snapshot is frozen, the record and the domain are not. The non-empty
    description invariant lives here, so every container enforces it
    identically. Activity and service fields (ref, dates, links) are
    model-specific and stay in the containing models.
    """

    title: Title
    employer: Employer
    description: str | None = None
    salary: Salary | None = None
    region: Region | None = None
    experience: Experience | None = None
    employment_type: EmploymentType | None = None
    work_format: WorkFormat | None = None
    grade: Grade | None = None
    specialization: Specialization | None = None
    skills: Skills = field(default_factory=Skills)

    def __post_init__(self) -> None:
        """Validate the non-empty description invariant."""
        if self.description is not None and not self.description.strip():
            msg = "description must not be empty"
            raise ValueError(msg)
