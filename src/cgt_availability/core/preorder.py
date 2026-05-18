"""Availability preorder over dependency-closed deficiency profiles."""

from __future__ import annotations

from cgt_availability.core.analyzer import AvailabilityAnalyzer
from cgt_availability.core.deficiency import Deficiency
from cgt_availability.core.package import ClaimPackage
from cgt_availability.core.serialization import json_dumps


def deficiency_profile_key(deficiency: Deficiency) -> tuple[str, str]:
    """Stable key for comparing dependency-closed deficiency profiles."""
    return (deficiency.code, json_dumps(deficiency.metadata))


def availability_preorder(
    less_available: ClaimPackage,
    more_available: ClaimPackage,
    *,
    analyzer: AvailabilityAnalyzer | None = None,
) -> bool:
    """Return whether the second package is at least as available as the first.

    The criterion follows the paper's preorder: package B is at least as available
    as package A when B has no more dependency-closed deficiencies than A.
    """
    active_analyzer = analyzer or AvailabilityAnalyzer.default()
    left_report = active_analyzer.analyze(less_available)
    right_report = active_analyzer.analyze(more_available)
    left = {deficiency_profile_key(item) for item in left_report.dependency_closed_deficiencies}
    right = {deficiency_profile_key(item) for item in right_report.dependency_closed_deficiencies}
    return right.issubset(left)
