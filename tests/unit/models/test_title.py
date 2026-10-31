"""Tests for the Title value object."""

from __future__ import annotations

import pytest

from vacancy_aggregator.core.models import Title


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("python developer", id="plain"),
        pytest.param("c++ developer", id="c-plus-plus"),
        pytest.param(".net developer", id="dotnet"),
    ],
)
def test_accepts_canonical_title(value: str) -> None:
    assert Title(value) == value


def test_title_is_a_string() -> None:
    title = Title("python developer")
    assert isinstance(title, str)
    assert title.upper() == "PYTHON DEVELOPER"


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("Python Developer", id="uppercase"),
        pytest.param("python  developer", id="multiple-spaces"),
        pytest.param(" python developer", id="leading-space"),
        pytest.param("python developer ", id="trailing-space"),
        pytest.param("", id="empty"),
    ],
)
def test_rejects_non_canonical_title(value: str) -> None:
    with pytest.raises(ValueError, match="title"):
        Title(value)
