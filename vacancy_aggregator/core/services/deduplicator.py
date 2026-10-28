"""Domain service: duplicate detection between a source and a domain vacancy."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vacancy_aggregator.core.models.domain_vacancy import DomainVacancy
    from vacancy_aggregator.core.models.source_vacancy import SourceVacancy


def is_duplicate(
    candidate: SourceVacancy,
    existing: DomainVacancy,
    *,
    window: timedelta = timedelta(days=30),
) -> bool:
    """Return True when the two vacancies are considered one and the same.

    All conditions must hold at once: the publication times differ by at most
    ``window`` (inclusive), and the titles, regions and employers match
    exactly. The fields are expected to be already normalized upstream, so
    this rule only compares values. A missing region on either side
    disqualifies the pair.
    """
    if abs(candidate.published_at - existing.published_at) > window:
        return False
    if candidate.title != existing.title:
        return False
    if candidate.region is None or existing.region is None:
        return False
    if candidate.region != existing.region:
        return False
    return candidate.employer == existing.employer
