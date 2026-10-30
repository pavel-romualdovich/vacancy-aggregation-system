"""Tests for the Region value object."""

from __future__ import annotations

import pytest

from vacancy_aggregator.core.models import Region


def test_accepts_canonical_region() -> None:
    assert Region("moscow") == "moscow"


def test_region_is_a_string() -> None:
    region = Region("moscow")
    assert isinstance(region, str)
    assert region.upper() == "MOSCOW"


def test_accepts_special_characters() -> None:
    assert Region("saint-petersburg") == "saint-petersburg"


def test_rejects_uppercase() -> None:
    with pytest.raises(ValueError, match="region"):
        Region("Moscow")


def test_rejects_multiple_spaces() -> None:
    with pytest.raises(ValueError, match="region"):
        Region("moscow  oblast")


def test_rejects_leading_space() -> None:
    with pytest.raises(ValueError, match="region"):
        Region(" moscow")


def test_rejects_trailing_space() -> None:
    with pytest.raises(ValueError, match="region"):
        Region("moscow ")


def test_rejects_empty() -> None:
    with pytest.raises(ValueError, match="region"):
        Region("")
