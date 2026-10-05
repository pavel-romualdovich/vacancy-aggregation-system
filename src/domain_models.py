from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class WorkFormat(StrEnum):
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    OFFICE = "Office"


class SeniorityLevel(StrEnum):
    INTERN = "Intern"
    JUNIOR = "Junior"
    MIDDLE = "Middle"
    SENIOR = "Senior"
    LEAD = "Lead"


class EmploymentType(StrEnum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    INTERNSHIP = "Internship"


class SalarySource(StrEnum):
    DECLARED = "Declared"
    PREDICTED = "Predicted"


@dataclass(frozen=True)
class Salary:
    from_: int | None = None
    to_: int | None = None
    currency: str | None = None
    source: SalarySource | None = None

    def __post_init__(self) -> None:
        if self.from_ is not None and self.from_ < 0:
            raise ValueError(
                f"Lower bound of salary (from_) cannot be negative: {self.from_}"
            )

        if self.to_ is not None and self.to_ < 0:
            raise ValueError(
                f"Upper bound of salary (to_) cannot be negative: {self.to_}"
            )

        if self.from_ is not None and self.to_ is not None and self.from_ > self.to_:
            raise ValueError(
                f"Upper salary bound (to_={self.to_}) cannot be less than"
                f"lower bound (from_={self.from_})"
            )

        if self.from_ is not None or self.to_ is not None:
            if not self.currency:
                raise ValueError("Currency is required when salary amount is set")
            if not self.source:
                raise ValueError("Source is required when salary amount is set")


@dataclass(frozen=True)
class Vacancy:
    id: int
    title: str
    seniority_level: SeniorityLevel
    is_active: bool
    skills: tuple[str, ...] = field(default_factory=tuple)
    work_format: WorkFormat = WorkFormat.OFFICE
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    min_exp_years: int = 0
    country: str = ""
    city: str = ""
    salary: Salary | None = None
    published: datetime | None = None

    def __post_init__(self) -> None:
        if self.id <= 0:
            raise ValueError(f"Vacancy id must be positive: {self.id}")

        if not self.title.strip():
            raise ValueError("Vacancy title cannot be empty")

        if self.min_exp_years < 0:
            raise ValueError(
                f"Minimum experience years cannot be negative: {self.min_exp_years}"
            )
