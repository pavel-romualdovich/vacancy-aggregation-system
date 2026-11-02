"""Domain service: duplicate detection between a source and a domain vacancy."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Final

from vacancy_aggregator.core.models.values import CandidateKey

if TYPE_CHECKING:
    from vacancy_aggregator.core.models.domain_vacancy import DomainVacancy
    from vacancy_aggregator.core.models.source_vacancy import SourceVacancy

DEFAULT_WINDOW: Final = timedelta(days=30)


def candidate_key(candidate: SourceVacancy) -> CandidateKey | None:
    """Build the repository lookup key for a source vacancy.

    The key mirrors the equality fields of :func:`is_duplicate` — employer,
    title and region. The rule demands a region on both sides, so a candidate
    without a region cannot be a duplicate and yields ``None`` (nothing to
    look up). Keeping the key next to the rule guarantees they never drift
    apart.
    """
    if candidate.business_fields.region is None:
        return None
    return CandidateKey(
        employer=candidate.business_fields.employer,
        title=candidate.business_fields.title,
        region=candidate.business_fields.region,
    )


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
    if candidate.business_fields.title != existing.business_fields.title:
        return False
    if (
        candidate.business_fields.region is None
        or existing.business_fields.region is None
    ):
        return False
    if candidate.business_fields.region != existing.business_fields.region:
        return False
    return candidate.business_fields.employer == existing.business_fields.employer
