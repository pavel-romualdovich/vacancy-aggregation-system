"""DomainVacancy — the single aggregated vacancy entity exposed to the API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from uuid6 import uuid7

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from vacancy_aggregator.core.models.vacancy_business_fields import (
        VacancyBusinessFields,
    )


@dataclass(kw_only=True)
class DomainVacancy:
    """One vacancy merged from all of its :class:`SourceVacancy` instances.

    The merged business data live in ``business_fields`` and result from the
    merge rules (freshness via ``detected_updated_at`` falling back to
    ``published_at``; an empty value never overwrites a filled one). No
    technical fields (source, source_id, url, service dates) live here, so
    they cannot leak into the API — the remaining fields are identity and
    lifecycle metadata.

    ``published_at`` is used for ordering and equals the maximum publication
    time across the linked source vacancies. The vacancy is active while at
    least one of its source vacancies is active; ``inactive_since`` is set
    exactly when the vacancy is inactive.
    """

    business_fields: VacancyBusinessFields
    published_at: datetime
    id: UUID = field(default_factory=uuid7)
    inactive_since: datetime | None = None

    @property
    def is_active(self) -> bool:
        """Whether the vacancy is currently active."""
        return self.inactive_since is None
