"""Tests for the Title value object."""

from __future__ import annotations

import pytest

from vacancy_aggregator.core.models import Title


def test_accepts_canonical_title() -> None:
    assert Title("python developer") == "python developer"


def test_title_is_a_string() -> None:
    title = Title("python developer")
    assert isinstance(title, str)
    assert title.upper() == "PYTHON DEVELOPER"


def test_accepts_special_characters() -> None:
    assert Title("c++ developer") == "c++ developer"
    assert Title(".net developer") == ".net developer"


def test_rejects_uppercase() -> None:
    with pytest.raises(ValueError, match="title"):
        Title("Python Developer")


def test_rejects_multiple_spaces() -> None:
    with pytest.raises(ValueError, match="title"):
        Title("python  developer")


def test_rejects_leading_space() -> None:
    with pytest.raises(ValueError, match="title"):
        Title(" python developer")


def test_rejects_trailing_space() -> None:
    with pytest.raises(ValueError, match="title"):
        Title("python developer ")


def test_rejects_empty() -> None:
    with pytest.raises(ValueError, match="title"):
        Title("")
