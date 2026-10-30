"""Domain service: normalization of raw source values into canonical models."""

from __future__ import annotations

import re

from vacancy_aggregator.core.models import Employer, Region, Title

# Legal form keywords removed from employer names. Extend this set to teach
# the normalizer about new forms — the rule itself stays untouched.
LEGAL_FORMS: frozenset[str] = frozenset(
    {"ооо", "зао", "ао", "пао", "оао", "ип", "чп"},
)

_SPECIALS_RE = re.compile(r"[^a-zа-яё0-9 ]+", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_employer(value: str) -> Employer:
    """Build a canonical Employer from a raw source value.

    The value is lowercased, special characters are removed, whitespace is
    collapsed, and legal form keywords (e.g. LLC-like prefixes) are dropped.
    Raises ``ValueError`` when nothing meaningful remains.
    """
    baseline = _employer_baseline(value)
    words = [word for word in baseline.split(" ") if word not in LEGAL_FORMS]
    result = " ".join(words)
    if not result:
        msg = "employer is empty after normalization"
        raise ValueError(msg)
    return Employer(result)


def normalize_title(value: str) -> Title:
    """Build a canonical Title from a raw source value.

    Only case and whitespace are normalized; special characters (e.g. "c++",
    ".net") are preserved. Raises ``ValueError`` when nothing remains.
    """
    result = _text_baseline(value)
    if not result:
        msg = "title is empty after normalization"
        raise ValueError(msg)
    return Title(result)


def normalize_region(value: str) -> Region:
    """Build a canonical Region from a raw source value.

    Only case and whitespace are normalized; special characters (e.g. "-" in
    "saint-petersburg") are preserved. Raises ``ValueError`` when nothing
    remains.
    """
    result = _text_baseline(value)
    if not result:
        msg = "region is empty after normalization"
        raise ValueError(msg)
    return Region(result)


def _text_baseline(value: str) -> str:
    """Lowercase and collapse whitespace, keeping special characters."""
    collapsed = _WHITESPACE_RE.sub(" ", value)
    return collapsed.strip().lower()


def _employer_baseline(value: str) -> str:
    """Text baseline with special characters replaced by spaces."""
    return _text_baseline(_SPECIALS_RE.sub(" ", value))
