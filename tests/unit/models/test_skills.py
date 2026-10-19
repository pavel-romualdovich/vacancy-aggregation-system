"""Tests for the Skills value object."""

from __future__ import annotations

import pytest

from vacancy_aggregator.core.models import Skills


def test_skills_rejects_non_normalized_skill() -> None:
    with pytest.raises(ValueError, match="skill"):
        Skills(["Python"])


def test_skills_rejects_empty_skill() -> None:
    with pytest.raises(ValueError, match="skill"):
        Skills([""])


def test_skills_accepts_normalized_skills() -> None:
    skills = Skills(["python", "django"])
    assert skills == frozenset({"python", "django"})


def test_skills_defaults_to_empty() -> None:
    assert Skills() == frozenset()


def test_skills_deduplicates_and_is_hashable() -> None:
    skills = Skills(["python", "python"])
    assert len(skills) == 1
    assert hash(skills) == hash(frozenset({"python"}))
