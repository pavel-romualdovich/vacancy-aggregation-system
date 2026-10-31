"""Fixtures and constants for the vacancy repository contract."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from tests.support import InMemoryVacancyRepository
from tests.support.builders import (
    DEFAULT_EMPLOYER,
    DEFAULT_REGION,
    DEFAULT_TITLE,
)

from vacancy_aggregator.core.models import CandidateKey
from vacancy_aggregator.core.ports import VacancyRepository

RepositoryFactory = Callable[[], VacancyRepository]

REPOSITORY_FACTORIES: list[RepositoryFactory] = [InMemoryVacancyRepository]

DEFAULT_KEY = CandidateKey(
    employer=DEFAULT_EMPLOYER,
    title=DEFAULT_TITLE,
    region=DEFAULT_REGION,
)


@pytest.fixture(params=REPOSITORY_FACTORIES, ids=lambda f: f.__name__.lower())
def repository(request: pytest.FixtureRequest) -> VacancyRepository:
    """Provide a fresh empty repository for every registered implementation."""
    factory: RepositoryFactory = request.param
    return factory()
