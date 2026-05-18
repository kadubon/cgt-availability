"""Optional plugin protocols.

These protocols describe integration boundaries only. Implementations should live
in optional packages or adapters so the core library remains dependency-free.
"""

from __future__ import annotations

from typing import Protocol

from cgt_availability.core.package import ClaimPackage
from cgt_availability.core.serialization import JSONValue
from cgt_availability.core.specs import ProvenanceRef


class StatisticalVerifierPlugin(Protocol):
    """Adapter boundary for statistical verifier packages."""

    name: str

    def verify(self, pkg: ClaimPackage) -> dict[str, JSONValue]:
        """Return a JSON-compatible verifier result without deciding truth."""


class ModelCheckingAdapter(Protocol):
    """Adapter boundary for external model-checking tools."""

    name: str

    def check(self, pkg: ClaimPackage) -> dict[str, JSONValue]:
        """Return a JSON-compatible model-checking result."""


class ProvenanceStore(Protocol):
    """Adapter boundary for external provenance stores."""

    name: str

    def resolve(self, reference: ProvenanceRef) -> dict[str, JSONValue]:
        """Resolve a provenance reference to JSON-compatible metadata."""


class MarkerAdapter(Protocol):
    """Adapter boundary for cgt-marker or equivalent marker-stream tools."""

    name: str

    def read_marker_state(self, pkg: ClaimPackage) -> dict[str, JSONValue]:
        """Return marker state without forcing a core dependency."""
