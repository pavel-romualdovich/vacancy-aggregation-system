"""SourceVacancy — normalized vacancy as seen in a single source."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from vacancy_aggregator.core.models.source_vacancy_snapshot import (
        SourceVacancySnapshot,
    )
    from vacancy_aggregator.core.models.vacancy_business_fields import (
        VacancyBusinessFields,
    )
    from vacancy_aggregator.core.models.values import SourceRef


@dataclass(kw_only=True)
class SourceVacancy:
    """A vacancy record coming from one specific source.

    The record is materialized from a :class:`SourceVacancySnapshot` by the
    resolver: the observed business data live in ``business_fields``, the
    service dates below are derived from the snapshot. Identity is the
    :class:`SourceRef` — ``(source, source_id)`` is globally unique. The
    service dates stay here and never leak into the public API. The public
    link is not stored: the adapter builds it from ``source_id`` on demand.
    ``domain_id`` links this observation to its merged
    :class:`DomainVacancy`; it is None until the resolver attaches the
    record.

    ``published_at`` is a snapshot taken on the first sight of the vacancy in
    the aggregator: it is never refreshed by later collections. If the source
    provides no publication date, the first collection time is used.
    ``last_seen_at`` is the moment of the latest observation and drives the
    activity logic. ``detected_updated_at`` is the moment the aggregator
    noticed a change in business fields or activity and never exceeds
    ``last_seen_at``. ``is_active`` follows the reported status and keeps the
    previous value when the source did not report one.
    """

    ref: SourceRef
    business_fields: VacancyBusinessFields
    published_at: datetime
    last_seen_at: datetime
    domain_id: UUID | None = None
    detected_updated_at: datetime | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate the detected/last_seen ordering."""
        if (
            self.detected_updated_at is not None
            and self.detected_updated_at > self.last_seen_at
        ):
            msg = "detected_updated_at must not be after last_seen_at"
            raise ValueError(msg)

    @classmethod
    def from_snapshot(cls, snapshot: SourceVacancySnapshot) -> SourceVacancy:
        """Build the first record for a source reference from an observation."""
        return cls(
            ref=snapshot.ref,
            business_fields=snapshot.business_fields,
            published_at=(
                snapshot.published_at
                if snapshot.published_at is not None
                else snapshot.collected_at
            ),
            last_seen_at=snapshot.collected_at,
            is_active=(snapshot.is_active if snapshot.is_active is not None else True),
        )
