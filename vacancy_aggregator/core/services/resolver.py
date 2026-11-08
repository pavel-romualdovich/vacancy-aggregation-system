"""Domain service: linking source vacancy snapshots to domain vacancies."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from vacancy_aggregator.core.models.source_vacancy import SourceVacancy
from vacancy_aggregator.core.services.deduplicator import (
    DEFAULT_WINDOW,
    candidate_key,
    is_duplicate,
)
from vacancy_aggregator.core.services.merger import build_domain_vacancy

if TYPE_CHECKING:
    from datetime import timedelta
    from uuid import UUID

    from vacancy_aggregator.core.models.domain_vacancy import DomainVacancy
    from vacancy_aggregator.core.models.source_vacancy_snapshot import (
        SourceVacancySnapshot,
    )
    from vacancy_aggregator.core.ports.repository import VacancyRepository


async def resolve_vacancy_snapshot(
    snapshot: SourceVacancySnapshot,
    repo: VacancyRepository,
    *,
    window: timedelta = DEFAULT_WINDOW,
) -> None:
    """Reconcile a single snapshot with the stored aggregate state.

    A snapshot whose source reference was never seen before materializes
    the first source vacancy record and links it to a domain vacancy. A
    record without a domain link is updated and the linking is retried:
    with exactly one duplicate the record is attached and the domain
    refreshed, with several it stays unlinked until the ambiguity
    resolves. A linked record is updated in place and its domain vacancy
    is refreshed only when the business fields or the activity changed.
    """
    stored_source_vacancy = await repo.find_source_vacancy(snapshot.ref)

    if stored_source_vacancy is None:
        created_source_vacancy = SourceVacancy.from_snapshot(snapshot)
        await _resolve_source_vacancy_linking(
            created_source_vacancy, repo, window=window
        )
        return

    built_updated_source_vacancy = _build_updated_source_vacancy(
        stored_source_vacancy, snapshot
    )

    if stored_source_vacancy.domain_id is None:
        await _resolve_source_vacancy_linking(
            built_updated_source_vacancy, repo, window=window
        )
    else:
        await repo.save_source_vacancy(built_updated_source_vacancy)
        if _snapshot_changes_source_vacancy(stored_source_vacancy, snapshot):
            await _refresh_domain_vacancy(stored_source_vacancy.domain_id, repo)


def _build_updated_source_vacancy(
    stored_source_vacancy: SourceVacancy,
    snapshot: SourceVacancySnapshot,
) -> SourceVacancy:
    """Return the stored source vacancy updated with a new snapshot.

    ``published_at`` is never refreshed by later snapshots;
    ``detected_updated_at`` records the moment the business fields or the
    activity changed.
    """
    new_is_active = (
        snapshot.is_active
        if snapshot.is_active is not None
        else stored_source_vacancy.is_active
    )
    new_detected_updated_at = (
        snapshot.collected_at
        if _snapshot_changes_source_vacancy(stored_source_vacancy, snapshot)
        else stored_source_vacancy.detected_updated_at
    )
    return replace(
        stored_source_vacancy,
        business_fields=snapshot.business_fields,
        last_seen_at=snapshot.collected_at,
        detected_updated_at=new_detected_updated_at,
        is_active=new_is_active,
    )


def _snapshot_changes_source_vacancy(
    stored_source_vacancy: SourceVacancy,
    snapshot: SourceVacancySnapshot,
) -> bool:
    """Return True when the snapshot differs from the stored source vacancy."""
    if stored_source_vacancy.business_fields != snapshot.business_fields:
        return True
    return (
        snapshot.is_active is not None
        and snapshot.is_active != stored_source_vacancy.is_active
    )


async def _resolve_source_vacancy_linking(
    source_vacancy: SourceVacancy,
    repo: VacancyRepository,
    *,
    window: timedelta,
) -> None:
    """Store the source vacancy record and link it to a domain vacancy.

    With no duplicates a fresh domain vacancy is created and linked; with
    exactly one the record is linked to it and the domain refreshed; with
    several the record is stored without a link until a later snapshot
    resolves the ambiguity.
    """
    domain_duplicates = await _find_domain_duplicates(
        source_vacancy, repo, window=window
    )
    match domain_duplicates:
        case []:
            built_domain_vacancy = build_domain_vacancy([source_vacancy])
            await repo.save_domain_vacancy(built_domain_vacancy)
            await repo.save_source_vacancy(
                replace(source_vacancy, domain_id=built_domain_vacancy.id)
            )
        case [existing_domain_vacancy]:
            await repo.save_source_vacancy(
                replace(source_vacancy, domain_id=existing_domain_vacancy.id)
            )
            await _refresh_domain_vacancy(existing_domain_vacancy.id, repo)
        case _:
            await repo.save_source_vacancy(source_vacancy)


async def _find_domain_duplicates(
    source_vacancy: SourceVacancy,
    repo: VacancyRepository,
    *,
    window: timedelta,
) -> list[DomainVacancy]:
    """Return the stored domain vacancies duplicating the given source record.

    Candidates are looked up by the deduplication key; a record without a
    region cannot be a duplicate and yields no candidates.
    """
    built_candidate_key = candidate_key(source_vacancy)
    if built_candidate_key is None:
        return []
    candidate_domain_vacancies = await repo.find_domain_candidates(built_candidate_key)
    return [
        existing_domain_vacancy
        for existing_domain_vacancy in candidate_domain_vacancies
        if is_duplicate(source_vacancy, existing_domain_vacancy, window=window)
    ]


async def _refresh_domain_vacancy(
    domain_vacancy_id: UUID,
    repo: VacancyRepository,
) -> None:
    """Refresh a stored domain vacancy from its linked source records."""
    linked_source_vacancies = await repo.find_sources_of(domain_vacancy_id)
    if not linked_source_vacancies:
        msg = f"domain vacancy {domain_vacancy_id} has no linked sources"
        raise LookupError(msg)
    built_domain_vacancy = build_domain_vacancy(linked_source_vacancies)
    await repo.save_domain_vacancy(replace(built_domain_vacancy, id=domain_vacancy_id))
