"""Domain service: building a DomainVacancy from source vacancies."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vacancy_aggregator.core.models.domain_vacancy import DomainVacancy
from vacancy_aggregator.core.models.vacancy_business_fields import (
    VacancyBusinessFields,
)
from vacancy_aggregator.core.models.values import Skills

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from datetime import datetime

    from vacancy_aggregator.core.models.source_vacancy import SourceVacancy


def build_domain_vacancy(sources: Sequence[SourceVacancy]) -> DomainVacancy:
    """Merge source vacancies into a single domain vacancy.

    Rules: a non-empty value always wins over an empty one; when both are
    present and differ, the value from the fresher source is used. Freshness
    is ``detected_updated_at`` falling back to ``published_at``; on equal
    freshness the smaller source name (lexicographic) wins, so the input
    order never affects the result for distinct sources. Skills are unioned;
    ``published_at`` is the maximum publication time across the sources;
    ``inactive_since`` is intentionally not set — the lifecycle logic
    derives it.
    """
    if not sources:
        msg = "at least one source vacancy is required"
        raise ValueError(msg)

    sources_by_preference = sorted(
        sources,
        key=lambda source: (
            -_get_freshness_date(source).timestamp(),
            source.ref.source,
        ),
    )

    return DomainVacancy(
        business_fields=VacancyBusinessFields(
            title=_require_field(
                sources_by_preference,
                lambda s: s.business_fields.title,
                "title",
            ),
            employer=_require_field(
                sources_by_preference,
                lambda s: s.business_fields.employer,
                "employer",
            ),
            description=_first_non_none(
                sources_by_preference, lambda s: s.business_fields.description
            ),
            salary=_first_non_none(
                sources_by_preference, lambda s: s.business_fields.salary
            ),
            region=_first_non_none(
                sources_by_preference, lambda s: s.business_fields.region
            ),
            experience=_first_non_none(
                sources_by_preference, lambda s: s.business_fields.experience
            ),
            employment_type=_first_non_none(
                sources_by_preference, lambda s: s.business_fields.employment_type
            ),
            work_format=_first_non_none(
                sources_by_preference, lambda s: s.business_fields.work_format
            ),
            grade=_first_non_none(
                sources_by_preference, lambda s: s.business_fields.grade
            ),
            specialization=_first_non_none(
                sources_by_preference, lambda s: s.business_fields.specialization
            ),
            skills=Skills(
                skill for source in sources for skill in source.business_fields.skills
            ),
        ),
        published_at=max(source.published_at for source in sources_by_preference),
    )


def _get_freshness_date(source: SourceVacancy) -> datetime:
    """Return the date used to compare source freshness.

    Uses ``detected_updated_at`` when available, otherwise falls back to
    ``published_at``.
    """
    return source.detected_updated_at or source.published_at


def _first_non_none[T](
    sources: Sequence[SourceVacancy],
    getter: Callable[[SourceVacancy], T | None],
) -> T | None:
    """Return the first non-None value in preference order, or None if all are None."""
    for source in sources:
        value = getter(source)
        if value is not None:
            return value
    return None


def _require_field[T](
    sources: Sequence[SourceVacancy],
    getter: Callable[[SourceVacancy], T | None],
    field_name: str,
) -> T:
    """Return the first non-None value in preference order, or raise if all are None."""
    value = _first_non_none(sources, getter)
    if value is None:
        msg = f"no source provides required field {field_name!r}"
        raise ValueError(msg)
    return value
