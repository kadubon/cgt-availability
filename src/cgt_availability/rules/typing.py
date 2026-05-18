"""Metadata-based report-path type checks."""

from __future__ import annotations

from cgt_availability.core.coherence import path_type_mismatches
from cgt_availability.core.deficiency import Deficiency, make_deficiency
from cgt_availability.core.package import ClaimPackage


def find_type_deficiencies(pkg: ClaimPackage) -> tuple[Deficiency, ...]:
    deficiencies: list[Deficiency] = []
    for left, right, left_codomain, right_domain in path_type_mismatches(pkg):
        deficiencies.append(
            make_deficiency(
                "report_path_type_error",
                message=(
                    f"{left}.codomain={left_codomain!r} is incompatible with "
                    f"{right}.domain={right_domain!r}."
                ),
                metadata={
                    "left": left,
                    "right": right,
                    "left_codomain": left_codomain,
                    "right_domain": right_domain,
                },
            )
        )
    return tuple(deficiencies)
