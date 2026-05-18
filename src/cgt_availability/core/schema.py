"""Public schema constants for cross-language interoperability."""

from __future__ import annotations

from cgt_availability.core.deficiency import DeficiencyCode

SCHEMA_VERSION = "1.0"
SCHEMA_ID_BASE = "https://github.com/kadubon/cgt-availability/schemas"
STABLE_DEFICIENCY_CODES: tuple[str, ...] = tuple(item.value for item in DeficiencyCode)


def schema_id(name: str) -> str:
    """Return a stable repository schema identifier."""
    return f"{SCHEMA_ID_BASE}/{name}.schema.json"
