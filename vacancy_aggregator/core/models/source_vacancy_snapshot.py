"""SourceVacancySnapshot — an immutable observation of a vacancy in one source."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from vacancy_aggregator.core.models.vacancy_business_fields import (
        VacancyBusinessFields,
    )
    from vacancy_aggregator.core.models.values import SourceRef


@dataclass(frozen=True, kw_only=True)
class SourceVacancySnapshot:
    """A transient, immutable observation of a vacancy in a single source.

    The adapter builds one snapshot per collected vacancy and passes it to the
    resolver, which materializes it into a stored :class:`SourceVacancy`
    record. The observed business data live in ``business_fields``; every
    other field here is a raw fact of the observation, not a decision:

    - ``ref`` — which source and which id;
    - ``published_at`` — the publication date as reported by the source, or
      ``None`` when the source did not report one. The decision (fall back to
      the first collection time, then freeze) belongs to the resolver;
    - ``collected_at`` — the moment of collection, the only source of time
      for the record (``last_seen_at``, and ``detected_updated_at`` on
      change);
    - ``is_active`` — the activity status as reported by the source, or
      ``None`` when the source did not report one. Treating a visible
      vacancy as active is the resolver's decision, not an observation.
    """

    ref: SourceRef
    business_fields: VacancyBusinessFields
    collected_at: datetime
    published_at: datetime | None = None
    is_active: bool | None = None
