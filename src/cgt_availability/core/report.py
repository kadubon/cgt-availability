"""Availability report data structure."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cgt_availability.core.deficiency import Deficiency
from cgt_availability.core.schema import SCHEMA_VERSION
from cgt_availability.core.serialization import (
    JSONValue,
    ensure_json_object,
    json_dumps,
    json_loads_object,
    string_dict,
    string_tuple,
)
from cgt_availability.core.status import AvailabilityProfile, AvailabilityStatus


@dataclass
class AvailabilityReport:
    """Result of analyzing a claim package."""

    claim_id: str
    status: AvailabilityStatus
    profile: AvailabilityProfile
    deficiencies: tuple[Deficiency, ...]
    dependency_closed_deficiencies: tuple[Deficiency, ...]
    warnings: tuple[str, ...]
    recommendations: tuple[str, ...]
    summary: str
    metadata: dict[str, JSONValue] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AvailabilityReport:
        deficiencies_value = data.get("deficiencies", ())
        closed_value = data.get("dependency_closed_deficiencies", ())
        if not isinstance(deficiencies_value, list | tuple):
            raise TypeError("deficiencies must be a sequence")
        if not isinstance(closed_value, list | tuple):
            raise TypeError("dependency_closed_deficiencies must be a sequence")
        return cls(
            claim_id=str(data["claim_id"]),
            status=AvailabilityStatus(str(data["status"])),
            profile=AvailabilityProfile.from_dict(
                data.get("profile", _legacy_profile_for_status(str(data["status"])))
            ),
            deficiencies=tuple(Deficiency.from_dict(item) for item in deficiencies_value),
            dependency_closed_deficiencies=tuple(
                Deficiency.from_dict(item) for item in closed_value
            ),
            warnings=string_tuple(data.get("warnings", ())),
            recommendations=string_tuple(data.get("recommendations", ())),
            summary=str(data["summary"]),
            metadata=string_dict(data.get("metadata", {})),
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
        )

    def to_json(self, *, indent: int | None = None) -> str:
        return json_dumps(self, indent=indent)

    @classmethod
    def from_json(cls, data: str) -> AvailabilityReport:
        return cls.from_dict(json_loads_object(data))


def _legacy_profile_for_status(status: str) -> dict[str, bool]:
    value = AvailabilityStatus(status)
    return {
        "is_partial": value in {AvailabilityStatus.PARTIAL, AvailabilityStatus.UNFORMED},
        "is_complete": value
        in {
            AvailabilityStatus.COMPLETE,
            AvailabilityStatus.WELL_TYPED,
            AvailabilityStatus.COHERENT,
            AvailabilityStatus.REPRODUCIBLY_AVAILABLE,
            AvailabilityStatus.CONTINUATION_SENSITIVE,
        },
        "is_well_typed": value
        in {
            AvailabilityStatus.WELL_TYPED,
            AvailabilityStatus.COHERENT,
            AvailabilityStatus.REPRODUCIBLY_AVAILABLE,
            AvailabilityStatus.CONTINUATION_SENSITIVE,
        },
        "is_coherent": value
        in {
            AvailabilityStatus.COHERENT,
            AvailabilityStatus.REPRODUCIBLY_AVAILABLE,
            AvailabilityStatus.CONTINUATION_SENSITIVE,
        },
        "is_reproducibly_available": value == AvailabilityStatus.REPRODUCIBLY_AVAILABLE,
        "is_continuation_sensitive": value == AvailabilityStatus.CONTINUATION_SENSITIVE,
        "is_blocked": value == AvailabilityStatus.BLOCKED,
    }
