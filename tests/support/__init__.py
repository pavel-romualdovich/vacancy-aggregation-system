"""Shared test doubles and builders."""

from tests.support.builders import (
    make_domain_vacancy,
    make_source_vacancy,
    make_source_vacancy_snapshot,
)
from tests.support.in_memory_repository import InMemoryVacancyRepository

__all__ = [
    "InMemoryVacancyRepository",
    "make_domain_vacancy",
    "make_source_vacancy",
    "make_source_vacancy_snapshot",
]
