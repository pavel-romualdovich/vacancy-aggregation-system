"""Storage port used by the vacancy resolver."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence
    from uuid import UUID

    from vacancy_aggregator.core.models.domain_vacancy import DomainVacancy
    from vacancy_aggregator.core.models.source_vacancy import SourceVacancy
    from vacancy_aggregator.core.models.values import CandidateKey, SourceRef


class VacancyRepository(Protocol):
    """Storage contract used by the vacancy resolver.

    The repository is deliberately dumb: it stores and retrieves records by
    key, and knows nothing about the deduplication rule. Searching for
    candidates happens via :class:`CandidateKey`, which the rule itself
    produces — the final verdict stays in :func:`is_duplicate`.
    """

    async def find_source_vacancy(self, ref: SourceRef) -> SourceVacancy | None:
        """Return the stored source vacancy for a ref, or None."""
        ...

    async def find_domain_candidates(
        self, key: CandidateKey
    ) -> Sequence[DomainVacancy]:
        """Return all domain vacancies matching a dedup lookup key.

        The result is a superset of the true duplicates: the caller still
        applies :func:`is_duplicate` to reach the verdict.
        """
        ...

    async def find_sources_of(self, domain_id: UUID) -> Sequence[SourceVacancy]:
        """Return every source vacancy linked to a domain vacancy."""
        ...

    async def save_source_vacancy(self, source: SourceVacancy) -> None:
        """Persist a source vacancy, upserting by ref."""
        ...

    async def save_domain_vacancy(self, domain: DomainVacancy) -> None:
        """Persist a domain vacancy, upserting by id."""
        ...
