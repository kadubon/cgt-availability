"""Marker-sensitive availability checks."""

from __future__ import annotations

from cgt_availability.core.deficiency import Deficiency, make_deficiency
from cgt_availability.core.diagnostics import diagnostic_requires_dimension
from cgt_availability.core.package import ClaimPackage


def find_marker_deficiencies(pkg: ClaimPackage) -> tuple[Deficiency, ...]:
    if diagnostic_requires_dimension(pkg, "marker") and (
        pkg.marker_policy is None or not pkg.marker_policy.declared
    ):
        return (make_deficiency("missing_marker_policy"),)
    if diagnostic_requires_dimension(pkg, "marker") and pkg.marker_policy is not None:
        deficiencies: list[Deficiency] = []
        marker_provenance = set(pkg.marker_policy.marker_provenance)
        if pkg.marker_state is not None:
            marker_provenance.update(pkg.marker_state.marker_provenance)
        if not marker_provenance:
            deficiencies.append(make_deficiency("missing_marker_provenance"))
        preserves_markers = pkg.marker_policy.preserves_markers or (
            pkg.marker_state is not None and pkg.marker_state.preserves_markers
        )
        if not pkg.marker_policy.tracks_unresolved or not preserves_markers:
            deficiencies.append(make_deficiency("marker_policy_incomplete", severity="blocking"))
        return tuple(deficiencies)
    return ()
