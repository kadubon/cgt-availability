"""Coarse availability labels."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from cgt_availability.core.serialization import JSONValue, ensure_json_object


class AvailabilityStatus(StrEnum):
    """Lossy summary labels for availability reports."""

    UNFORMED = "unformed"
    PARTIAL = "partial"
    COMPLETE = "complete"
    WELL_TYPED = "well_typed"
    COHERENT = "coherent"
    REPRODUCIBLY_AVAILABLE = "reproducibly_available"
    CONTINUATION_SENSITIVE = "continuation_sensitive"
    BLOCKED = "blocked"


class CoarseAvailabilityClass(StrEnum):
    """Paper-style coarse labels A0-A9; lossy and secondary to profiles."""

    A0_UNFORMED = "A0"
    A1_EXPRESSIVE = "A1"
    A2_PROJECTED = "A2"
    A3_OBSERVABLE = "A3"
    A4_NORMALIZED = "A4"
    A5_VERIFIABLE = "A5"
    A6_OPERATIONALLY_FALSIFIABLE = "A6"
    A7_REPRODUCIBLE = "A7"
    A8_SCIENTIFICALLY_AVAILABLE = "A8"
    A9_ROBUSTLY_AVAILABLE = "A9"


@dataclass(frozen=True)
class AvailabilityProfile:
    """Layered availability facts; coarse status is a lossy summary of this profile."""

    is_partial: bool
    is_complete: bool
    is_well_typed: bool
    is_coherent: bool
    is_reproducibly_available: bool
    is_continuation_sensitive: bool
    is_blocked: bool

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AvailabilityProfile:
        return cls(
            is_partial=bool(data.get("is_partial", False)),
            is_complete=bool(data.get("is_complete", False)),
            is_well_typed=bool(data.get("is_well_typed", False)),
            is_coherent=bool(data.get("is_coherent", False)),
            is_reproducibly_available=bool(data.get("is_reproducibly_available", False)),
            is_continuation_sensitive=bool(data.get("is_continuation_sensitive", False)),
            is_blocked=bool(data.get("is_blocked", False)),
        )


def coarse_availability_class(report: Any) -> CoarseAvailabilityClass:
    """Return a lossy A0-A9 label derived from an availability report."""
    codes = {item.code for item in report.dependency_closed_deficiencies}
    metadata = getattr(report, "metadata", {})
    if {"missing_frame", "missing_system"} & codes:
        return CoarseAvailabilityClass.A0_UNFORMED
    if "missing_projection" in codes:
        return CoarseAvailabilityClass.A1_EXPRESSIVE
    if "missing_observation" in codes or "missing_description" in codes:
        return CoarseAvailabilityClass.A2_PROJECTED
    if "missing_normalizer" in codes or "report_path_type_error" in codes:
        return CoarseAvailabilityClass.A3_OBSERVABLE
    if "missing_verifier" in codes or "missing_expected_report" in codes:
        return CoarseAvailabilityClass.A4_NORMALIZED
    if "missing_failure_predicate" in codes:
        return CoarseAvailabilityClass.A5_VERIFIABLE
    if "missing_reproduction_protocol" in codes:
        return CoarseAvailabilityClass.A6_OPERATIONALLY_FALSIFIABLE
    if report.profile.is_reproducibly_available and bool(metadata.get("robust_available")):
        return CoarseAvailabilityClass.A9_ROBUSTLY_AVAILABLE
    if report.profile.is_reproducibly_available:
        return CoarseAvailabilityClass.A8_SCIENTIFICALLY_AVAILABLE
    if "missing_reproduction_protocol" not in codes:
        return CoarseAvailabilityClass.A7_REPRODUCIBLE
    return CoarseAvailabilityClass.A0_UNFORMED
