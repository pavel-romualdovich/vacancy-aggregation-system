"""Tests for the build_domain_vacancy merge service."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest
from tests.support.builders import (
    PUBLISHED_AT,
    make_source_vacancy,
)

from vacancy_aggregator.core.models import (
    Currency,
    Employer,
    EmploymentType,
    Experience,
    Grade,
    Region,
    Salary,
    Skills,
    SourceRef,
    SourceVacancy,
    Specialization,
    Title,
    WorkFormat,
)
from vacancy_aggregator.core.services.merger import build_domain_vacancy

NEWER_PUBLISHED = PUBLISHED_AT + timedelta(days=1)
DETECTED_LATER = PUBLISHED_AT + timedelta(days=2)
LATEST_SEEN = PUBLISHED_AT + timedelta(days=3)


def source_ref(source: str, source_id: str = "1") -> SourceRef:
    """Build a SourceRef from a source name and an id."""
    return SourceRef(source=source, source_id=source_id)


def make_fresh_source(**overrides: object) -> SourceVacancy:
    """Build a source vacancy fresher than the default one."""
    return make_source_vacancy(
        detected_updated_at=DETECTED_LATER,
        last_seen_at=LATEST_SEEN,
        **overrides,
    )


def test_raises_on_empty_input() -> None:
    with pytest.raises(ValueError, match="at least one"):
        build_domain_vacancy([])


def test_single_source_is_projected() -> None:
    salary = Salary(
        from_amount=100_000, to_amount=150_000, currency=Currency.RUB, gross=True
    )
    source = make_source_vacancy(
        description="desc",
        salary=salary,
        region=Region("moscow"),
        skills=Skills(["python", "django"]),
    )
    vacancy = build_domain_vacancy([source])
    assert vacancy.title == "python developer"
    assert vacancy.employer == "acme"
    assert vacancy.description == "desc"
    assert vacancy.salary == salary
    assert vacancy.region == "moscow"
    assert vacancy.skills == Skills(["python", "django"])
    assert vacancy.published_at == PUBLISHED_AT
    assert vacancy.is_active is True
    assert vacancy.inactive_since is None


def test_identical_values_are_preserved() -> None:
    sources = [
        make_source_vacancy(ref=SourceRef("hh", "1"), region=Region("moscow")),
        make_source_vacancy(ref=SourceRef("hh", "2"), region=Region("moscow")),
    ]
    assert build_domain_vacancy(sources).region == "moscow"


def test_non_empty_wins_over_empty_regardless_of_freshness() -> None:
    fresher = make_fresh_source(description=None)
    older = make_source_vacancy(ref=SourceRef("hh", "2"), description="filled")
    assert build_domain_vacancy([fresher, older]).description == "filled"


def test_fresher_value_wins_when_both_present() -> None:
    older = make_source_vacancy(
        ref=SourceRef("hh", "1"),
        description="old",
        detected_updated_at=PUBLISHED_AT,
    )
    fresher = make_fresh_source(ref=SourceRef("hh", "2"), description="new")
    assert build_domain_vacancy([older, fresher]).description == "new"


def test_freshness_falls_back_to_published_at() -> None:
    older = make_source_vacancy(ref=SourceRef("hh", "1"), description="old")
    fresher = make_source_vacancy(
        ref=SourceRef("hh", "2"),
        description="new",
        published_at=NEWER_PUBLISHED,
    )
    assert build_domain_vacancy([older, fresher]).description == "new"


def test_equal_freshness_prefers_smaller_source() -> None:
    source_larger = make_source_vacancy(ref=source_ref("zz"), description="second")
    source_smaller = make_source_vacancy(ref=source_ref("aa"), description="first")
    vacancy = build_domain_vacancy([source_larger, source_smaller])
    assert vacancy.description == "first"


def test_equal_freshness_and_source_id_prefers_smaller_source() -> None:
    first = make_source_vacancy(ref=source_ref("hh"), description="from_hh")
    second = make_source_vacancy(ref=source_ref("sj"), description="from_sj")
    vacancy = build_domain_vacancy([first, second])
    assert vacancy.description == "from_hh"


def test_result_is_order_independent() -> None:
    older = make_source_vacancy(
        ref=SourceRef("hh", "b"),
        description="old",
        detected_updated_at=PUBLISHED_AT,
    )
    fresher = make_fresh_source(ref=SourceRef("hh", "a"), description="new")

    forward = build_domain_vacancy([older, fresher])
    backward = build_domain_vacancy([fresher, older])

    assert forward.description == backward.description == "new"
    assert forward.region == backward.region
    assert forward.skills == backward.skills
    assert forward.title == backward.title


def test_input_sources_are_not_mutated() -> None:
    source = make_source_vacancy(
        description="keep",
        region=Region("moscow"),
        skills=Skills(["python"]),
    )
    snapshot = (
        source.description,
        source.region,
        source.skills,
        source.detected_updated_at,
    )
    build_domain_vacancy([source])
    assert (
        source.description,
        source.region,
        source.skills,
        source.detected_updated_at,
    ) == snapshot


def test_all_empty_optional_fields_merge_to_none() -> None:
    sources = [
        make_source_vacancy(ref=SourceRef("hh", "1"), region=None),
        make_source_vacancy(ref=SourceRef("hh", "2"), region=None),
    ]
    vacancy = build_domain_vacancy(sources)
    assert vacancy.description is None
    assert vacancy.region is None
    assert vacancy.salary is None
    assert vacancy.experience is None


@pytest.mark.parametrize(
    ("field", "older_value", "fresher_value"),
    [
        ("title", Title("old title"), Title("new title")),
        ("description", "old", "new"),
        ("region", Region("old"), Region("new")),
        ("employer", Employer("oldco"), Employer("newco")),
        ("experience", Experience.FROM_1_TO_3, Experience.MORE_THAN_6),
        ("employment_type", EmploymentType.PART_TIME, EmploymentType.FULL_TIME),
        ("work_format", WorkFormat.REMOTE, WorkFormat.HYBRID),
        ("grade", Grade.MIDDLE, Grade.SENIOR),
        ("specialization", Specialization.BACKEND, Specialization.FULLSTACK),
    ],
)
def test_all_scalar_fields_merge_by_freshness(
    field: str,
    older_value: object,
    fresher_value: object,
) -> None:
    older = make_source_vacancy(
        ref=SourceRef("hh", "older"),
        detected_updated_at=PUBLISHED_AT,
    )
    fresher = make_fresh_source(ref=SourceRef("hh", "fresher"))
    older = replace(older, **{field: older_value})
    fresher = replace(fresher, **{field: fresher_value})

    vacancy = build_domain_vacancy([older, fresher])
    assert getattr(vacancy, field) == fresher_value


def test_detected_updated_at_outranks_published_at() -> None:
    with_detected = make_fresh_source(
        ref=SourceRef("hh", "1"),
        description="from_detected",
    )
    newer_published = make_source_vacancy(
        ref=SourceRef("hh", "2"),
        description="from_published",
        published_at=NEWER_PUBLISHED,
    )
    vacancy = build_domain_vacancy([newer_published, with_detected])
    assert vacancy.description == "from_detected"


def test_skills_are_union() -> None:
    sources = [
        make_source_vacancy(ref=SourceRef("hh", "1"), skills=Skills(["python"])),
        make_source_vacancy(
            ref=SourceRef("hh", "2"), skills=Skills(["django", "python"])
        ),
    ]
    assert build_domain_vacancy(sources).skills == Skills(["python", "django"])


def test_published_at_is_max_across_sources() -> None:
    sources = [
        make_source_vacancy(ref=SourceRef("hh", "1"), published_at=PUBLISHED_AT),
        make_source_vacancy(ref=SourceRef("hh", "2"), published_at=NEWER_PUBLISHED),
    ]
    assert build_domain_vacancy(sources).published_at == NEWER_PUBLISHED


def test_published_at_is_not_affected_by_detected_updated_at() -> None:
    fresher_detected = make_fresh_source(
        ref=SourceRef("hh", "1"),
        published_at=PUBLISHED_AT,
    )
    newer_published = make_source_vacancy(
        ref=SourceRef("hh", "2"),
        published_at=NEWER_PUBLISHED,
    )
    vacancy = build_domain_vacancy([fresher_detected, newer_published])
    assert vacancy.published_at == NEWER_PUBLISHED


def test_salary_non_empty_wins_over_empty() -> None:
    salary = Salary(
        from_amount=100_000, to_amount=150_000, currency=Currency.RUB, gross=False
    )
    sources = [
        make_source_vacancy(ref=SourceRef("hh", "1"), salary=None),
        make_source_vacancy(ref=SourceRef("hh", "2"), salary=salary),
    ]
    assert build_domain_vacancy(sources).salary == salary


def test_salary_fresher_wins_when_both_present() -> None:
    older = Salary(
        from_amount=90_000, to_amount=120_000, currency=Currency.RUB, gross=False
    )
    fresher = Salary(
        from_amount=110_000, to_amount=160_000, currency=Currency.RUB, gross=False
    )
    sources = [
        make_source_vacancy(
            ref=SourceRef("hh", "1"),
            salary=older,
            detected_updated_at=PUBLISHED_AT,
        ),
        make_fresh_source(ref=SourceRef("hh", "2"), salary=fresher),
    ]
    assert build_domain_vacancy(sources).salary == fresher
