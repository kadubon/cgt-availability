"""Continuation-sensitive availability checks."""

from __future__ import annotations

from cgt_availability.core.deficiency import Deficiency, make_deficiency
from cgt_availability.core.diagnostics import diagnostic_requires_dimension
from cgt_availability.core.package import ClaimPackage
from cgt_availability.core.residual import has_residual_scientific_space


def find_continuation_deficiencies(pkg: ClaimPackage) -> tuple[Deficiency, ...]:
    if diagnostic_requires_dimension(pkg, "continuation") and (
        pkg.continuation is None or not pkg.continuation.declared
    ):
        return (make_deficiency("missing_continuation"),)
    if (
        diagnostic_requires_dimension(pkg, "continuation")
        and pkg.continuation is not None
        and not pkg.continuation.diagnostic_name
    ):
        return (make_deficiency("missing_continuation_diagnostic"),)
    return ()


def continuation_warnings(pkg: ClaimPackage) -> tuple[str, ...]:
    if pkg.continuation is None:
        return ()
    if not has_residual_scientific_space(pkg):
        return (
            "Continuation is declared, but no residual constraints, follow-up tests, "
            "refinement paths, or repair paths are declared.",
        )
    return ()
