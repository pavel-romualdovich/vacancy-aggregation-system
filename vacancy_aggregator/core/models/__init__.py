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
from vacancy_aggregator.core.models.source_vacancy_snapshot import (
    SourceVacancySnapshot,
)
from vacancy_aggregator.core.models.vacancy_business_fields import (
    VacancyBusinessFields,
)
from vacancy_aggregator.core.models.values import (
    CandidateKey,
    Employer,
    Region,
    Salary,
    Skills,
    SourceRef,
    Title,
)

__all__ = [
    "CandidateKey",
    "Currency",
    "DomainVacancy",
    "Employer",
    "EmploymentType",
    "Experience",
    "Grade",
    "Region",
    "Salary",
    "Skills",
    "SourceRef",
    "SourceVacancy",
    "SourceVacancySnapshot",
    "Specialization",
    "Title",
    "VacancyBusinessFields",
    "WorkFormat",
    "uuid7",
]
