"""Tests for the Employer value object."""

from __future__ import annotations

import pytest

from vacancy_aggregator.core.models import Employer


def test_accepts_canonical_employer() -> None:
    assert Employer("acme") == "acme"


def test_accepts_employer_with_legal_form_prefix() -> None:
    assert Employer("llc romashka") == "llc romashka"


def test_employer_is_a_string() -> None:
    employer = Employer("acme")
    assert isinstance(employer, str)
    assert employer.upper() == "ACME"


def test_rejects_uppercase() -> None:
    with pytest.raises(ValueError, match="employer"):
        Employer("Acme")


def test_rejects_special_characters() -> None:
    with pytest.raises(ValueError, match="employer"):
        Employer("acme&co")


def test_rejects_multiple_spaces() -> None:
    with pytest.raises(ValueError, match="employer"):
        Employer("acme  co")


def test_rejects_leading_space() -> None:
    with pytest.raises(ValueError, match="employer"):
        Employer(" acme")


def test_rejects_trailing_space() -> None:
    with pytest.raises(ValueError, match="employer"):
        Employer("acme ")


def test_rejects_empty() -> None:
    with pytest.raises(ValueError, match="employer"):
        Employer("")
