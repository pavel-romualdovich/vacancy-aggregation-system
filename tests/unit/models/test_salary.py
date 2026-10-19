"""Tests for the Salary value object invariants."""

from __future__ import annotations

import pytest

from vacancy_aggregator.core.models import Currency, Salary


def make_salary(
    from_amount: int | None = 100,
    to_amount: int | None = 200,
    currency: Currency = Currency.RUB,
    gross: bool = False,
) -> Salary:
    """Build a Salary with convenient defaults."""
    return Salary(
        from_amount=from_amount,
        to_amount=to_amount,
        currency=currency,
        gross=gross,
    )


def test_salary_requires_at_least_one_bound() -> None:
    with pytest.raises(ValueError, match="at least one bound"):
        make_salary(from_amount=None, to_amount=None)


def test_salary_accepts_only_from_amount() -> None:
    salary = make_salary(to_amount=None)
    assert salary.from_amount == 100
    assert salary.to_amount is None


def test_salary_accepts_only_to_amount() -> None:
    salary = make_salary(from_amount=None)
    assert salary.from_amount is None
    assert salary.to_amount == 200


def test_salary_accepts_both_bounds() -> None:
    salary = make_salary(from_amount=100, to_amount=200)
    assert salary.from_amount == 100
    assert salary.to_amount == 200


def test_salary_accepts_equal_bounds() -> None:
    salary = make_salary(from_amount=100, to_amount=100)
    assert salary.from_amount == salary.to_amount


def test_salary_rejects_from_above_to() -> None:
    with pytest.raises(ValueError, match="must not exceed"):
        make_salary(from_amount=200, to_amount=100)


def test_salary_rejects_zero_from_amount() -> None:
    with pytest.raises(ValueError, match="positive"):
        make_salary(from_amount=0)


def test_salary_rejects_zero_to_amount() -> None:
    with pytest.raises(ValueError, match="positive"):
        make_salary(to_amount=0)


def test_salary_rejects_negative_bounds() -> None:
    with pytest.raises(ValueError, match="positive"):
        make_salary(from_amount=-100)
    with pytest.raises(ValueError, match="positive"):
        make_salary(to_amount=-200)
