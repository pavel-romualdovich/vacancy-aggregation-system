"""Domain enums for vacancy aggregation."""

from __future__ import annotations

from enum import StrEnum


class Currency(StrEnum):
    """Supported currencies for salaries."""

    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class Experience(StrEnum):
    """Required experience level, following the common industry scale."""

    NO_EXPERIENCE = "no_experience"
    FROM_1_TO_3 = "from_1_to_3"
    FROM_3_TO_6 = "from_3_to_6"
    MORE_THAN_6 = "more_than_6"


class EmploymentType(StrEnum):
    """Employment type. Internships are expressed via :class:`Grade.INTERN`."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"


class WorkFormat(StrEnum):
    """Work location format. Unknown format is represented by ``None``."""

    REMOTE = "remote"
    OFFICE = "office"
    HYBRID = "hybrid"


class Grade(StrEnum):
    """Seniority grade as reported by the source."""

    INTERN = "intern"
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"


class Specialization(StrEnum):
    """Coarse IT specialization used for filtering and analytics."""

    BACKEND = "backend"
    FRONTEND = "frontend"
    FULLSTACK = "fullstack"
    MOBILE = "mobile"
    DEVOPS = "devops"
    DATA_SCIENCE = "data_science"
    QA = "qa"
    ANALYST = "analyst"
    DESIGN = "design"
    PRODUCT_MANAGER = "product_manager"
    OTHER = "other"
