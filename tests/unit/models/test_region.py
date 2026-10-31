"""Tests for the Region value object."""

from __future__ import annotations

import pytest

from vacancy_aggregator.core.models import Region


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("moscow", id="plain"),
        pytest.param("saint-petersburg", id="special-characters"),
    ],
)
def test_accepts_canonical_region(value: str) -> None:
    assert Region(value) == value


def test_region_is_a_string() -> None:
    region = Region("moscow")
    assert isinstance(region, str)
    assert region.upper() == "MOSCOW"


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("Moscow", id="uppercase"),
        pytest.param("moscow  oblast", id="multiple-spaces"),
        pytest.param(" moscow", id="leading-space"),
        pytest.param("moscow ", id="trailing-space"),
        pytest.param("", id="empty"),
    ],
)
def test_rejects_non_canonical_region(value: str) -> None:
    with pytest.raises(ValueError, match="region"):
        Region(value)
