"""Tests for the normalization services."""

from __future__ import annotations

import pytest

from vacancy_aggregator.core.models import Employer, Region, Title
from vacancy_aggregator.core.services.normalizer import (
    normalize_employer,
    normalize_region,
    normalize_title,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ООО Ромашка", "ромашка"),
        ("ЗАО Ромашка", "ромашка"),
        ("АО Ромашка", "ромашка"),
        ("ПАО Ромашка", "ромашка"),
        ("ОАО Ромашка", "ромашка"),
        ("ИП Иванов", "иванов"),
        ("ЧП Сидоров", "сидоров"),
    ],
)
def test_legal_forms_are_removed(raw: str, expected: str) -> None:
    assert normalize_employer(raw) == Employer(expected)


def test_no_legal_form() -> None:
    assert normalize_employer("Ромашка") == Employer("ромашка")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Ромашка&Ко", "ромашка ко"),
        ("ООО «Ромашка-Плюс»", "ромашка плюс"),
        ("Ромашка, ООО", "ромашка"),
    ],
)
def test_special_characters_are_removed(raw: str, expected: str) -> None:
    assert normalize_employer(raw) == Employer(expected)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('ООО "Ромашка"', "ромашка"),
        ("ООО «Ромашка»", "ромашка"),
    ],
)
def test_quotes_are_removed(raw: str, expected: str) -> None:
    assert normalize_employer(raw) == Employer(expected)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ООО Ромашка", "ромашка"),
        ("ооо ромашка", "ромашка"),
        ("Ооо РОМАШКА", "ромашка"),
    ],
)
def test_case_is_normalized(raw: str, expected: str) -> None:
    assert normalize_employer(raw) == Employer(expected)


def test_whitespace_is_collapsed() -> None:
    raw = "  ООО   Ромашка  "
    assert normalize_employer(raw) == Employer("ромашка")


def test_rejects_when_nothing_left() -> None:
    with pytest.raises(ValueError, match="employer"):
        normalize_employer("ООО")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Python Developer", "python developer"),
        ("C++ Developer", "c++ developer"),
        (".Net Backend Developer", ".net backend developer"),
        ("PYTHON", "python"),
    ],
)
def test_title_case_is_normalized(raw: str, expected: str) -> None:
    assert normalize_title(raw) == Title(expected)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("C++ Developer", "c++ developer"),
        (".NET Backend", ".net backend"),
        ("Python (middle)", "python (middle)"),
        ("Java/Kotlin", "java/kotlin"),
    ],
)
def test_title_special_characters_are_preserved(raw: str, expected: str) -> None:
    assert normalize_title(raw) == Title(expected)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Python   Developer  ", "python developer"),
        ("python\tdeveloper\n", "python developer"),
    ],
)
def test_title_whitespace_is_collapsed(raw: str, expected: str) -> None:
    assert normalize_title(raw) == Title(expected)


@pytest.mark.parametrize("raw", ["", "   ", "\t\n"])
def test_title_rejects_empty(raw: str) -> None:
    with pytest.raises(ValueError, match="title"):
        normalize_title(raw)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Москва", "москва"),
        ("Санкт-Петербург", "санкт-петербург"),
        ("Saint-Petersburg", "saint-petersburg"),
        ("Нью-Йорк", "нью-йорк"),
    ],
)
def test_region_case_is_normalized(raw: str, expected: str) -> None:
    assert normalize_region(raw) == Region(expected)


def test_region_whitespace_is_collapsed() -> None:
    assert normalize_region("  Санкт-Петербург   область  ") == Region(
        "санкт-петербург область"
    )


@pytest.mark.parametrize("raw", ["", "   "])
def test_region_rejects_empty(raw: str) -> None:
    with pytest.raises(ValueError, match="region"):
        normalize_region(raw)
