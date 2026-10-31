"""Tests for the Skills value object."""

from __future__ import annotations

import pytest

from vacancy_aggregator.core.models import Skills


@pytest.mark.parametrize(
    "values",
    [
        pytest.param(["Python"], id="uppercase"),
        pytest.param([""], id="empty-skill"),
        pytest.param([" python "], id="untrimmed"),
    ],
)
def test_rejects_non_normalized_skill(values: list[str]) -> None:
    with pytest.raises(ValueError, match="skill"):
        Skills(values)


def test_accepts_normalized_skills() -> None:
    assert Skills(["python", "django"]) == frozenset({"python", "django"})


def test_defaults_to_empty() -> None:
    assert Skills() == frozenset()


def test_deduplicates_and_is_hashable() -> None:
    skills = Skills(["python", "python"])
    assert len(skills) == 1
    assert hash(skills) == hash(frozenset({"python"}))
