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


@pytest.mark.parametrize(
    ("from_amount", "to_amount"),
    [
        pytest.param(100, None, id="only-from"),
        pytest.param(None, 200, id="only-to"),
        pytest.param(100, 200, id="both-bounds"),
        pytest.param(100, 100, id="equal-bounds"),
    ],
)
def test_accepts_valid_bounds(from_amount: int | None, to_amount: int | None) -> None:
    salary = make_salary(from_amount=from_amount, to_amount=to_amount)
    assert salary.from_amount == from_amount
    assert salary.to_amount == to_amount


def test_requires_at_least_one_bound() -> None:
    with pytest.raises(ValueError, match="at least one bound"):
        make_salary(from_amount=None, to_amount=None)


def test_rejects_from_above_to() -> None:
    with pytest.raises(ValueError, match="must not exceed"):
        make_salary(from_amount=200, to_amount=100)


@pytest.mark.parametrize(
    ("from_amount", "to_amount"),
    [
        pytest.param(0, None, id="zero-from"),
        pytest.param(None, 0, id="zero-to"),
        pytest.param(-100, None, id="negative-from"),
        pytest.param(None, -200, id="negative-to"),
    ],
)
def test_rejects_non_positive_bounds(
    from_amount: int | None, to_amount: int | None
) -> None:
    with pytest.raises(ValueError, match="positive"):
        make_salary(from_amount=from_amount, to_amount=to_amount)
