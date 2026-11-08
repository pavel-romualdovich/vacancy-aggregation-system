"""Tests for the resolve_vacancy_snapshot orchestration service."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any, get_type_hints
from uuid import UUID

import pytest
from tests.support import InMemoryVacancyRepository
from tests.support.builders import (
    LAST_SEEN_AT,
    PUBLISHED_AT,
    make_domain_vacancy,
    make_source_vacancy,
    make_source_vacancy_snapshot,
)

from vacancy_aggregator.core.models import (
    CandidateKey,
    Currency,
    DomainVacancy,
    Employer,
    Region,
    Salary,
    Skills,
    SourceRef,
    SourceVacancy,
    SourceVacancySnapshot,
    Title,
    VacancyBusinessFields,
)
from vacancy_aggregator.core.services.merger import build_domain_vacancy
from vacancy_aggregator.core.services.resolver import resolve_vacancy_snapshot

LATER_SEEN = LAST_SEEN_AT + timedelta(days=1)
MUCH_LATER_SEEN = LAST_SEEN_AT + timedelta(days=2)
BEYOND_WINDOW_PUBLISHED = PUBLISHED_AT - timedelta(days=31)

HH_REF = SourceRef(source="hh", source_id="1")
HABR_REF = SourceRef(source="habr", source_id="7")
OTHER_REGION = Region("kazan")
OTHER_TITLE = Title("data engineer")
OTHER_EMPLOYER = Employer("globex")


# --------------------------------------------------------------------------
# Helpers — everything is observed through the repository port only
# --------------------------------------------------------------------------


def make_salary(amount: int) -> Salary:
    return Salary(from_amount=amount, to_amount=None, currency=Currency.RUB, gross=True)


async def stored_domain(
    repo: InMemoryVacancyRepository, domain: DomainVacancy
) -> DomainVacancy | None:
    """Return the stored domain vacancy with the same id, or None."""
    if domain.business_fields.region is None:
        return None
    key = CandidateKey(
        employer=domain.business_fields.employer,
        title=domain.business_fields.title,
        region=domain.business_fields.region,
    )
    for candidate in await repo.find_domain_candidates(key):
        if candidate.id == domain.id:
            return candidate
    return None


async def is_untouched(repo: InMemoryVacancyRepository, domain: DomainVacancy) -> bool:
    """Return True when the domain vacancy was saved and never rewritten."""
    return await stored_domain(repo, domain) is domain


async def domain_of(repo: InMemoryVacancyRepository, ref: SourceRef) -> DomainVacancy:
    """Return the domain vacancy an observation is linked to."""
    source = await repo.find_source_vacancy(ref)
    assert source is not None
    assert source.domain_id is not None
    for domain in await repo.find_domain_candidates(
        CandidateKey(
            employer=source.business_fields.employer,
            title=source.business_fields.title,
            region=source.business_fields.region,  # type: ignore[arg-type]
        )
    ):
        if domain.id == source.domain_id:
            return domain
    pytest.fail(f"linked domain {source.domain_id} is not found")


async def link(
    repo: InMemoryVacancyRepository, source: SourceVacancy
) -> tuple[SourceVacancy, DomainVacancy]:
    """Persist a source vacancy together with its materialized domain."""
    domain = build_domain_vacancy([source])
    await repo.save_domain_vacancy(domain)
    linked = replace(source, domain_id=domain.id)
    await repo.save_source_vacancy(linked)
    return linked, domain


def reobserve(
    record: SourceVacancy,
    *,
    collected_at: datetime = LATER_SEEN,
    **overrides: Any,
) -> SourceVacancySnapshot:
    """Build a snapshot from the current state of a stored record."""
    kwargs: dict[str, Any] = {
        "ref": record.ref,
        "title": record.business_fields.title,
        "published_at": record.published_at,
        "collected_at": collected_at,
        "employer": record.business_fields.employer,
        "description": record.business_fields.description,
        "salary": record.business_fields.salary,
        "region": record.business_fields.region,
        "skills": record.business_fields.skills,
        "is_active": record.is_active,
    }
    kwargs.update(overrides)
    return make_source_vacancy_snapshot(**kwargs)


# --------------------------------------------------------------------------
# No link yet
# --------------------------------------------------------------------------


async def test_first_observation_creates_domain() -> None:
    repo = InMemoryVacancyRepository()
    candidate = make_source_vacancy_snapshot(ref=HH_REF)

    await resolve_vacancy_snapshot(candidate, repo)

    stored = await repo.find_source_vacancy(HH_REF)
    assert stored is not None
    assert stored.detected_updated_at is None
    assert stored.published_at == candidate.published_at
    domain = await domain_of(repo, HH_REF)
    assert domain.business_fields.title == candidate.business_fields.title
    assert domain.business_fields.employer == candidate.business_fields.employer
    assert domain.business_fields.region == candidate.business_fields.region
    assert domain.published_at == candidate.published_at
    assert list(await repo.find_sources_of(domain.id)) == [stored]


async def test_missing_region_skips_candidate_search_and_creates() -> None:
    repo = InMemoryVacancyRepository()
    neighbour = make_domain_vacancy()
    await repo.save_domain_vacancy(neighbour)

    await resolve_vacancy_snapshot(
        make_source_vacancy_snapshot(ref=HH_REF, region=None), repo
    )

    created = await domain_of(repo, HH_REF)
    assert created.id != neighbour.id
    assert created.business_fields.region is None
    assert await is_untouched(repo, neighbour)


@pytest.mark.parametrize(
    "snapshot",
    [
        pytest.param(
            make_source_vacancy_snapshot(
                ref=HH_REF, published_at=BEYOND_WINDOW_PUBLISHED
            ),
            id="outside-window",
        ),
        pytest.param(
            make_source_vacancy_snapshot(ref=HH_REF, title=OTHER_TITLE),
            id="different-title",
        ),
        pytest.param(
            make_source_vacancy_snapshot(ref=HH_REF, employer=OTHER_EMPLOYER),
            id="different-employer",
        ),
        pytest.param(
            make_source_vacancy_snapshot(ref=HH_REF, region=OTHER_REGION),
            id="different-region",
        ),
    ],
)
async def test_not_a_duplicate_creates_new_domain(
    snapshot: SourceVacancySnapshot,
) -> None:
    repo = InMemoryVacancyRepository()
    neighbour = make_domain_vacancy()
    await repo.save_domain_vacancy(neighbour)

    await resolve_vacancy_snapshot(snapshot, repo)

    stored = await repo.find_source_vacancy(HH_REF)
    assert stored is not None
    assert stored.detected_updated_at is None
    created = await domain_of(repo, HH_REF)
    assert created.id != neighbour.id
    assert created.business_fields.title == snapshot.business_fields.title
    assert created.business_fields.employer == snapshot.business_fields.employer
    assert await is_untouched(repo, neighbour)


# --------------------------------------------------------------------------
# No link yet — exactly one duplicate candidate
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("domain_kwargs", "candidate_kwargs", "expected_field", "expected_value"),
    [
        pytest.param(
            {"description": "old"},
            {"description": "new"},
            "description",
            "new",
            id="description",
        ),
        pytest.param(
            {"salary": make_salary(100_000)},
            {"salary": make_salary(150_000)},
            "salary",
            make_salary(150_000),
            id="salary",
        ),
        pytest.param(
            {"skills": Skills({"python"})},
            {"skills": Skills({"go"})},
            "skills",
            Skills({"go"}),
            id="skills-from-fresher-source",
        ),
    ],
)
async def test_single_candidate_links_and_rebuilds_domain(
    domain_kwargs: dict[str, Any],
    candidate_kwargs: dict[str, Any],
    expected_field: str,
    expected_value: object,
) -> None:
    repo = InMemoryVacancyRepository()
    _, existing = await link(repo, make_source_vacancy(ref=HABR_REF))
    await repo.save_domain_vacancy(
        replace(
            existing,
            business_fields=replace(existing.business_fields, **domain_kwargs),
        )
    )
    candidate = make_source_vacancy_snapshot(ref=HH_REF, **candidate_kwargs)

    await resolve_vacancy_snapshot(candidate, repo)

    stored = await repo.find_source_vacancy(HH_REF)
    assert stored is not None
    assert stored.domain_id == existing.id
    domain = await domain_of(repo, HH_REF)
    assert domain.id == existing.id
    assert getattr(domain.business_fields, expected_field) == expected_value
    assert {source.ref for source in await repo.find_sources_of(domain.id)} == {
        HABR_REF,
        HH_REF,
    }


async def test_linking_merges_previously_linked_sources() -> None:
    repo = InMemoryVacancyRepository()
    _, existing = await link(
        repo, make_source_vacancy(ref=HABR_REF, skills=Skills({"go"}))
    )
    candidate = make_source_vacancy_snapshot(ref=HH_REF, skills=Skills({"python"}))

    await resolve_vacancy_snapshot(candidate, repo)

    stored = await repo.find_source_vacancy(HH_REF)
    assert stored is not None
    assert stored.domain_id == existing.id
    domain = await domain_of(repo, HH_REF)
    assert domain.id == existing.id
    assert domain.business_fields.skills == Skills({"go", "python"})
    assert {source.ref for source in await repo.find_sources_of(domain.id)} == {
        HABR_REF,
        HH_REF,
    }
    other = await repo.find_source_vacancy(HABR_REF)
    assert other is not None
    assert other.domain_id == existing.id


# --------------------------------------------------------------------------
# No link yet — ambiguous candidates
# --------------------------------------------------------------------------


async def test_multiple_candidates_leave_observation_unlinked() -> None:
    repo = InMemoryVacancyRepository()
    first = make_domain_vacancy()
    second = make_domain_vacancy()
    await repo.save_domain_vacancy(first)
    await repo.save_domain_vacancy(second)

    await resolve_vacancy_snapshot(make_source_vacancy_snapshot(ref=HH_REF), repo)

    stored = await repo.find_source_vacancy(HH_REF)
    assert stored is not None
    assert stored.domain_id is None
    assert stored.detected_updated_at is None
    assert await is_untouched(repo, first)
    assert await is_untouched(repo, second)
    assert first.business_fields.region is not None
    key = CandidateKey(
        employer=first.business_fields.employer,
        title=first.business_fields.title,
        region=first.business_fields.region,
    )
    assert list(await repo.find_domain_candidates(key)) == [first, second]


# --------------------------------------------------------------------------
# No link yet — repeated sighting of an unlinked observation
# --------------------------------------------------------------------------


async def test_repeated_unlinked_sighting_links_once_ambiguity_resolves() -> None:
    repo = InMemoryVacancyRepository()
    first = make_domain_vacancy()
    second = make_domain_vacancy()
    await repo.save_domain_vacancy(first)
    await repo.save_domain_vacancy(second)
    await resolve_vacancy_snapshot(make_source_vacancy_snapshot(ref=HH_REF), repo)
    # Moving the second candidate out of the window leaves one duplicate.
    narrowed_second = replace(second, published_at=BEYOND_WINDOW_PUBLISHED)
    await repo.save_domain_vacancy(narrowed_second)
    stored = await repo.find_source_vacancy(HH_REF)
    assert stored is not None

    await resolve_vacancy_snapshot(reobserve(stored, description="new"), repo)

    after = await repo.find_source_vacancy(HH_REF)
    assert after is not None
    assert after.domain_id == first.id
    assert after.detected_updated_at == LATER_SEEN
    assert after.published_at == PUBLISHED_AT
    rebuilt = await domain_of(repo, HH_REF)
    assert rebuilt.business_fields.description == "new"
    narrowed = await stored_domain(repo, narrowed_second)
    assert narrowed is not None
    assert narrowed.business_fields.description is None


async def test_still_ambiguous_unlinked_sighting_stays_unlinked() -> None:
    repo = InMemoryVacancyRepository()
    first = make_domain_vacancy()
    second = make_domain_vacancy()
    await repo.save_domain_vacancy(first)
    await repo.save_domain_vacancy(second)
    await resolve_vacancy_snapshot(make_source_vacancy_snapshot(ref=HH_REF), repo)
    stored = await repo.find_source_vacancy(HH_REF)
    assert stored is not None

    await resolve_vacancy_snapshot(reobserve(stored), repo)

    after = await repo.find_source_vacancy(HH_REF)
    assert after is not None
    assert after.domain_id is None
    assert after.last_seen_at == LATER_SEEN
    assert after.detected_updated_at is None
    assert await is_untouched(repo, first)
    assert await is_untouched(repo, second)


# --------------------------------------------------------------------------
# Link already exists
# --------------------------------------------------------------------------


async def test_linked_sighting_without_changes_only_touches_last_seen() -> None:
    repo = InMemoryVacancyRepository()
    stored, domain = await link(repo, make_source_vacancy(ref=HH_REF))

    await resolve_vacancy_snapshot(reobserve(stored), repo)

    after = await repo.find_source_vacancy(HH_REF)
    assert after is not None
    assert after.last_seen_at == LATER_SEEN
    assert after.detected_updated_at is None
    assert replace(after, last_seen_at=stored.last_seen_at) == stored
    assert await is_untouched(repo, domain)


async def test_linked_sighting_without_changes_keeps_detected_stamp() -> None:
    repo = InMemoryVacancyRepository()
    stored, domain = await link(
        repo,
        replace(make_source_vacancy(ref=HH_REF), detected_updated_at=LAST_SEEN_AT),
    )

    await resolve_vacancy_snapshot(reobserve(stored), repo)

    after = await repo.find_source_vacancy(HH_REF)
    assert after is not None
    assert after.detected_updated_at == LAST_SEEN_AT
    assert await is_untouched(repo, domain)


@pytest.mark.parametrize(
    ("change", "field"),
    [
        pytest.param({"description": "new"}, "description", id="description"),
        pytest.param({"salary": make_salary(200_000)}, "salary", id="salary"),
        pytest.param({"region": Region("spb")}, "region", id="region"),
    ],
)
async def test_linked_sighting_with_changes_updates_detected_stamp(
    change: dict[str, Any], field: str
) -> None:
    repo = InMemoryVacancyRepository()
    stored, domain = await link(repo, make_source_vacancy(ref=HH_REF))
    snapshot = reobserve(stored, **change)

    await resolve_vacancy_snapshot(snapshot, repo)

    after = await repo.find_source_vacancy(HH_REF)
    assert after is not None
    assert after.detected_updated_at == LATER_SEEN
    assert getattr(after.business_fields, field) == getattr(
        snapshot.business_fields, field
    )
    assert after.published_at == stored.published_at
    assert after.domain_id == domain.id
    rebuilt = await domain_of(repo, HH_REF)
    assert rebuilt.id == domain.id
    assert getattr(rebuilt.business_fields, field) == getattr(
        snapshot.business_fields, field
    )


async def test_linked_change_never_touches_published_at() -> None:
    repo = InMemoryVacancyRepository()
    await link(repo, make_source_vacancy(ref=HH_REF))

    await resolve_vacancy_snapshot(
        make_source_vacancy_snapshot(
            ref=HH_REF,
            published_at=PUBLISHED_AT + timedelta(days=10),
            collected_at=LATER_SEEN,
            description="new",
        ),
        repo,
    )

    after = await repo.find_source_vacancy(HH_REF)
    assert after is not None
    assert after.published_at == PUBLISHED_AT
    rebuilt = await domain_of(repo, HH_REF)
    assert rebuilt.published_at == PUBLISHED_AT


@pytest.mark.parametrize(
    "change",
    [
        pytest.param({"title": OTHER_TITLE}, id="title"),
        pytest.param({"employer": OTHER_EMPLOYER}, id="employer"),
        pytest.param({"region": OTHER_REGION}, id="region"),
    ],
)
async def test_linked_observation_keeps_link_when_key_fields_drift(
    change: dict[str, Any],
) -> None:
    repo = InMemoryVacancyRepository()
    stored, domain = await link(repo, make_source_vacancy(ref=HH_REF))
    snapshot = reobserve(stored, **change)
    drifted = next(iter(change))

    await resolve_vacancy_snapshot(snapshot, repo)

    after = await repo.find_source_vacancy(HH_REF)
    assert after is not None
    assert after.domain_id == domain.id
    rebuilt = await domain_of(repo, HH_REF)
    assert rebuilt.id == domain.id
    assert getattr(rebuilt.business_fields, drifted) == getattr(
        snapshot.business_fields, drifted
    )


async def test_linked_deactivation_updates_snapshot_but_not_lifecycle() -> None:
    repo = InMemoryVacancyRepository()
    stored, _ = await link(repo, make_source_vacancy(ref=HH_REF))

    await resolve_vacancy_snapshot(reobserve(stored, is_active=False), repo)

    after = await repo.find_source_vacancy(HH_REF)
    assert after is not None
    assert after.is_active is False
    assert after.detected_updated_at == LATER_SEEN
    rebuilt = await domain_of(repo, HH_REF)
    assert rebuilt.inactive_since is None


async def test_linked_multiple_changes_apply_all_at_once() -> None:
    repo = InMemoryVacancyRepository()
    _, domain = await link(repo, make_source_vacancy(ref=HH_REF))

    await resolve_vacancy_snapshot(
        make_source_vacancy_snapshot(
            ref=HH_REF,
            collected_at=MUCH_LATER_SEEN,
            title=OTHER_TITLE,
            employer=OTHER_EMPLOYER,
            region=OTHER_REGION,
            description="new",
            skills=Skills({"python"}),
        ),
        repo,
    )

    after = await repo.find_source_vacancy(HH_REF)
    assert after is not None
    assert after.detected_updated_at == MUCH_LATER_SEEN
    assert after.business_fields.title == OTHER_TITLE
    assert after.business_fields.employer == OTHER_EMPLOYER
    assert after.business_fields.region == OTHER_REGION
    rebuilt = await domain_of(repo, HH_REF)
    assert rebuilt.id == domain.id
    assert rebuilt.business_fields.title == OTHER_TITLE
    assert rebuilt.business_fields.employer == OTHER_EMPLOYER
    assert rebuilt.business_fields.region == OTHER_REGION
    assert rebuilt.business_fields.description == "new"
    assert rebuilt.business_fields.skills == Skills({"python"})


# --------------------------------------------------------------------------
# Field list, idempotency and time semantics
# --------------------------------------------------------------------------


def test_business_fields_annotation_on_vacancy_models() -> None:
    """All three vacancy models carry ``business_fields: VacancyBusinessFields``."""
    localns: dict[str, object] = {
        "datetime": datetime,
        "UUID": UUID,
        "SourceRef": SourceRef,
        "VacancyBusinessFields": VacancyBusinessFields,
    }
    for cls in (SourceVacancySnapshot, SourceVacancy, DomainVacancy):
        annotations = get_type_hints(cls, localns=localns)
        assert annotations["business_fields"] is VacancyBusinessFields


async def test_first_observation_keeps_snapshot_published_at() -> None:
    repo = InMemoryVacancyRepository()
    published = PUBLISHED_AT - timedelta(days=5)

    await resolve_vacancy_snapshot(
        make_source_vacancy_snapshot(ref=HH_REF, published_at=published), repo
    )

    stored = await repo.find_source_vacancy(HH_REF)
    assert stored is not None
    assert stored.published_at == published


async def test_first_observation_without_reported_date_uses_collection_time() -> None:
    repo = InMemoryVacancyRepository()

    await resolve_vacancy_snapshot(
        make_source_vacancy_snapshot(
            ref=HH_REF, published_at=None, collected_at=LATER_SEEN
        ),
        repo,
    )

    stored = await repo.find_source_vacancy(HH_REF)
    assert stored is not None
    assert stored.published_at == LATER_SEEN


async def test_sighting_date_beyond_window_uses_frozen_record_published_at() -> None:
    """The dedup window uses the record's frozen published_at, not the snapshot's."""
    repo = InMemoryVacancyRepository()
    first = make_domain_vacancy()
    second = make_domain_vacancy()
    await repo.save_domain_vacancy(first)
    await repo.save_domain_vacancy(second)
    await resolve_vacancy_snapshot(make_source_vacancy_snapshot(ref=HH_REF), repo)
    narrowed_second = replace(second, published_at=BEYOND_WINDOW_PUBLISHED)
    await repo.save_domain_vacancy(narrowed_second)

    await resolve_vacancy_snapshot(
        make_source_vacancy_snapshot(
            ref=HH_REF,
            published_at=PUBLISHED_AT + timedelta(days=40),
            collected_at=LATER_SEEN,
        ),
        repo,
    )

    stored = await repo.find_source_vacancy(HH_REF)
    assert stored is not None
    assert stored.domain_id == first.id
    assert stored.published_at == PUBLISHED_AT
    assert first.business_fields.region is not None
    key = CandidateKey(
        employer=first.business_fields.employer,
        title=first.business_fields.title,
        region=first.business_fields.region,
    )
    assert list(await repo.find_domain_candidates(key)) == [first, narrowed_second]


async def test_custom_window_widens_duplicate_search() -> None:
    repo = InMemoryVacancyRepository()
    existing = make_domain_vacancy(published_at=PUBLISHED_AT - timedelta(days=40))
    await repo.save_domain_vacancy(existing)

    await resolve_vacancy_snapshot(
        make_source_vacancy_snapshot(ref=HH_REF), repo, window=timedelta(days=60)
    )

    stored = await repo.find_source_vacancy(HH_REF)
    assert stored is not None
    assert stored.domain_id == existing.id


async def test_repeated_identical_resolutions_are_idempotent() -> None:
    repo = InMemoryVacancyRepository()
    candidate = make_source_vacancy_snapshot(ref=HH_REF, description="new")

    await resolve_vacancy_snapshot(candidate, repo)
    snapshot = await repo.find_source_vacancy(HH_REF)
    domain = await domain_of(repo, HH_REF)

    await resolve_vacancy_snapshot(candidate, repo)

    assert await repo.find_source_vacancy(HH_REF) == snapshot
    assert await domain_of(repo, HH_REF) is domain


# --------------------------------------------------------------------------
# No link yet — one duplicate candidate after the snapshot drifted
# --------------------------------------------------------------------------


async def test_unlinked_sighting_without_changes_links() -> None:
    repo = InMemoryVacancyRepository()
    first = make_domain_vacancy()
    second = make_domain_vacancy()
    await repo.save_domain_vacancy(first)
    await repo.save_domain_vacancy(second)
    await resolve_vacancy_snapshot(make_source_vacancy_snapshot(ref=HH_REF), repo)
    await repo.save_domain_vacancy(
        replace(
            second,
            business_fields=replace(second.business_fields, title=OTHER_TITLE),
        )
    )
    stored = await repo.find_source_vacancy(HH_REF)
    assert stored is not None

    await resolve_vacancy_snapshot(reobserve(stored), repo)

    after = await repo.find_source_vacancy(HH_REF)
    assert after is not None
    assert after.domain_id == first.id
    assert after.detected_updated_at is None


# --------------------------------------------------------------------------
# Link already exists — reactivation
# --------------------------------------------------------------------------


async def test_linked_reactivation_updates_snapshot_and_detection_stamp() -> None:
    repo = InMemoryVacancyRepository()
    stored, domain = await link(
        repo,
        replace(make_source_vacancy(ref=HH_REF), is_active=False),
    )

    await resolve_vacancy_snapshot(reobserve(stored, is_active=True), repo)

    after = await repo.find_source_vacancy(HH_REF)
    assert after is not None
    assert after.is_active is True
    assert after.detected_updated_at == LATER_SEEN
    rebuilt = await domain_of(repo, HH_REF)
    assert rebuilt.id == domain.id
    assert rebuilt.inactive_since is None
