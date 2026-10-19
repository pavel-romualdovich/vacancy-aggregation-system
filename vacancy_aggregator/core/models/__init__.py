"""Domain models: enums, value objects and vacancy entities."""

from uuid6 import uuid7

from vacancy_aggregator.core.models.domain_vacancy import DomainVacancy
from vacancy_aggregator.core.models.enums import (
    Currency,
    EmploymentType,
    Experience,
    Grade,
    Specialization,
    WorkFormat,
)
from vacancy_aggregator.core.models.source_vacancy import SourceVacancy
from vacancy_aggregator.core.models.values import Salary, Skills, SourceRef

__all__ = [
    "Currency",
    "DomainVacancy",
    "EmploymentType",
    "Experience",
    "Grade",
    "Salary",
    "Skills",
    "SourceRef",
    "SourceVacancy",
    "Specialization",
    "WorkFormat",
    "uuid7",
]
