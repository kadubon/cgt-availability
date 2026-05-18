"""Practical report-factorization diagnostics."""

from __future__ import annotations

from cgt_availability.core.deficiency import Deficiency, make_deficiency
from cgt_availability.core.diagnostics import (
    diagnostic_requires_dimension,
    report_omits_dimension,
    requested_diagnostics,
)
from cgt_availability.core.package import ClaimPackage

REPORT_FACTOR_DIMENSIONS = ("history", "marker", "continuation")


def find_report_factorization_deficiencies(pkg: ClaimPackage) -> tuple[Deficiency, ...]:
    deficiencies: list[Deficiency] = []
    dimensions = set(REPORT_FACTOR_DIMENSIONS)
    dimensions.update(requested_diagnostics(pkg))
    if pkg.projection is not None:
        omitted = pkg.projection.metadata.get("omits_dimensions", ())
        if isinstance(omitted, str):
            dimensions.add(omitted)
        elif isinstance(omitted, list | tuple):
            dimensions.update(str(item) for item in omitted)
    for dimension in sorted(dimensions):
        if diagnostic_requires_dimension(pkg, dimension) and report_omits_dimension(pkg, dimension):
            deficiencies.append(
                make_deficiency(
                    "report_only_insufficiency_risk",
                    message=(
                        f"Report-only diagnosis is insufficient for requested {dimension!r} "
                        "diagnostics because the projection declares that dimension omitted."
                    ),
                    metadata={"dimension": dimension},
                )
            )
    return tuple(deficiencies)
