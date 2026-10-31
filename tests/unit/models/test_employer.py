"""Tests for the Employer value object."""

from __future__ import annotations

import pytest

from vacancy_aggregator.core.models import Employer


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("acme", id="plain"),
        pytest.param("llc romashka", id="legal-form-prefix"),
    ],
)
def test_accepts_canonical_employer(value: str) -> None:
    assert Employer(value) == value


def test_employer_is_a_string() -> None:
    employer = Employer("acme")
    assert isinstance(employer, str)
    assert employer.upper() == "ACME"


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("Acme", id="uppercase"),
        pytest.param("acme&co", id="special-characters"),
        pytest.param("acme  co", id="multiple-spaces"),
        pytest.param(" acme", id="leading-space"),
        pytest.param("acme ", id="trailing-space"),
        pytest.param("", id="empty"),
    ],
)
def test_rejects_non_canonical_employer(value: str) -> None:
    with pytest.raises(ValueError, match="employer"):
        Employer(value)
