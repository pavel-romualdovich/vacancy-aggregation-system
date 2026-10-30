"""Domain value objects shared across vacancy models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from vacancy_aggregator.core.models.enums import Currency


def _is_canonical(value: str, *, no_specials: bool) -> bool:
    """Return True when the value is already in canonical text form.

    Single pass, no allocations: no uppercase letters, words separated by
    single spaces, no leading or trailing whitespace. With ``no_specials``
    any non-letter/digit character also disqualifies the value. Legal form
    prefixes are allowed — removing them is the normalizer's job.
    """
    prev_space = True
    for ch in value:
        if ch == " ":
            if prev_space:
                return False
            prev_space = True
        elif ch.islower() or ch.isdigit():
            prev_space = False
        elif no_specials or ch.isupper():
            return False
        else:
            prev_space = False
    return not prev_space


class Employer(str):
    """Canonical employer name; the invariant is enforced on construction."""

    def __new__(cls, value: str) -> Employer:
        """Create an Employer, rejecting non-canonical values."""
        if not _is_canonical(value, no_specials=True):
            msg = "employer must be in canonical form"
            raise ValueError(msg)
        return super().__new__(cls, value)


class Title(str):
    """Canonical vacancy title; the invariant is enforced on construction.

    Special characters are preserved (e.g. "c++ developer") — only case and
    spacing are canonicalized.
    """

    def __new__(cls, value: str) -> Title:
        """Create a Title, rejecting non-canonical values."""
        if not _is_canonical(value, no_specials=False):
            msg = "title must be in canonical form"
            raise ValueError(msg)
        return super().__new__(cls, value)


class Region(str):
    """Canonical region name; the invariant is enforced on construction.

    Special characters are preserved (e.g. "saint-petersburg") — only case
    and spacing are canonicalized.
    """

    def __new__(cls, value: str) -> Region:
        """Create a Region, rejecting non-canonical values."""
        if not _is_canonical(value, no_specials=False):
            msg = "region must be in canonical form"
            raise ValueError(msg)
        return super().__new__(cls, value)


class Skills(frozenset[str]):
    """Immutable set of normalized skills.

    Every skill must be non-empty, trimmed and lower-cased — the format
    guaranteed by the normalizer and enforced on construction.
    """

    def __new__(cls, values: Iterable[str] = ()) -> Skills:
        """Create a Skills set, rejecting any non-normalized skill."""
        normalized = frozenset(values)
        for skill in normalized:
            if not skill or skill != skill.strip().lower():
                msg = f"skill {skill!r} is not normalized (lowercase, trimmed)"
                raise ValueError(msg)
        return super().__new__(cls, normalized)


@dataclass(frozen=True)
class Salary:
    """Salary range in the currency of publication.

    Amounts are expressed in whole units of the currency (e.g. rubles, not
    kopecks). At least one bound must be present, both bounds must be
    positive, and ``from_amount`` must not exceed ``to_amount`` when both are
    set.
    """

    from_amount: int | None
    to_amount: int | None
    currency: Currency
    gross: bool

    def __post_init__(self) -> None:
        """Validate salary invariants: positivity, ordering and bounds."""
        if self.from_amount is not None and self.from_amount <= 0:
            msg = "from_amount must be positive"
            raise ValueError(msg)
        if self.to_amount is not None and self.to_amount <= 0:
            msg = "to_amount must be positive"
            raise ValueError(msg)
        if (
            self.from_amount is not None
            and self.to_amount is not None
            and self.from_amount > self.to_amount
        ):
            msg = "from_amount must not exceed to_amount"
            raise ValueError(msg)
        if self.from_amount is None and self.to_amount is None:
            msg = "salary must have at least one bound"
            raise ValueError(msg)


@dataclass(frozen=True)
class SourceRef:
    """Composite identity of a vacancy within a single source."""

    source: str
    source_id: str
