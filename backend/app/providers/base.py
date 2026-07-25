from collections.abc import AsyncIterator
from typing import Protocol

from app.domain.imports import ImportCandidate


class ProviderAdapter(Protocol):
    """Boundary implemented independently by each collection provider."""

    code: str

    def discover(self, *, limit: int) -> AsyncIterator[ImportCandidate]: ...
