"""In-memory vacancy repository used in tests and local runs."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from uuid import UUID

    from vacancy_aggregator.core.models.domain_vacancy import DomainVacancy
    from vacancy_aggregator.core.models.source_vacancy import SourceVacancy
    from vacancy_aggregator.core.models.values import CandidateKey, SourceRef


class InMemoryVacancyRepository:
    """A trivial VacancyRepository backed by dicts.

    Records are stored by key and returned as tuples. Sufficient for unit
    tests of the resolver and for contract tests of other implementations.
    """

    def __init__(self) -> None:
        """Create an empty repository."""
        self._sources: dict[SourceRef, SourceVacancy] = {}
        self._domains: dict[UUID, DomainVacancy] = {}

    async def find_source_vacancy(self, ref: SourceRef) -> SourceVacancy | None:
        """Return the stored source vacancy for a ref, or None."""
        return self._sources.get(ref)

    async def find_domain_candidates(
        self, key: CandidateKey
    ) -> Sequence[DomainVacancy]:
        """Return all domain vacancies matching a dedup lookup key."""
        return tuple(
            domain
            for domain in self._domains.values()
            if (
                domain.business_fields.employer,
                domain.business_fields.title,
                domain.business_fields.region,
            )
            == (key.employer, key.title, key.region)
        )

    async def find_sources_of(self, domain_id: UUID) -> Sequence[SourceVacancy]:
        """Return every source vacancy linked to a domain vacancy."""
        return tuple(
            source for source in self._sources.values() if source.domain_id == domain_id
        )

    async def save_source_vacancy(self, source: SourceVacancy) -> None:
        """Persist a source vacancy, upserting by ref."""
        self._sources[source.ref] = source

    async def save_domain_vacancy(self, domain: DomainVacancy) -> None:
        """Persist a domain vacancy, upserting by id."""
        self._domains[domain.id] = domain
