"""Required component checks."""

from __future__ import annotations

from cgt_availability.core.deficiency import Deficiency, make_deficiency
from cgt_availability.core.diagnostics import diagnostic_requires_dimension
from cgt_availability.core.package import ClaimPackage
from cgt_availability.core.specs import BaseSpec

CORE_COMPONENTS: tuple[tuple[str, str], ...] = (
    ("frame", "missing_frame"),
    ("system", "missing_system"),
    ("projection", "missing_projection"),
    ("observation", "missing_observation"),
    ("description", "missing_description"),
    ("normalizer", "missing_normalizer"),
    ("expected_report", "missing_expected_report"),
    ("verifier", "missing_verifier"),
    ("failure_predicate", "missing_failure_predicate"),
    ("reproduction_protocol", "missing_reproduction_protocol"),
)


def is_missing(spec: BaseSpec | None) -> bool:
    return spec is None or not spec.declared


def find_required_component_deficiencies(pkg: ClaimPackage) -> tuple[Deficiency, ...]:
    deficiencies: list[Deficiency] = []
    for component_name, code in CORE_COMPONENTS:
        if is_missing(getattr(pkg, component_name)):
            deficiencies.append(make_deficiency(code))

    if comparison_required(pkg) and not comparison_declared(pkg):
        deficiencies.append(make_deficiency("missing_comparison_regime"))

    if not pkg.provenance:
        deficiencies.append(make_deficiency("missing_provenance"))

    if diagnostic_requires_dimension(pkg, "history") and is_missing(pkg.history):
        deficiencies.append(make_deficiency("missing_history"))

    return tuple(deficiencies)


def comparison_required(pkg: ClaimPackage) -> bool:
    return bool(pkg.metadata.get("comparison_required", False))


def comparison_declared(pkg: ClaimPackage) -> bool:
    if pkg.comparison_regime is not None and pkg.comparison_regime.declared:
        return True
    if pkg.metadata.get("comparison_regime") is not None:
        return True
    for spec in (pkg.frame, pkg.system, pkg.projection):
        if spec is not None and spec.metadata.get("comparison_regime") is not None:
            return True
    return False
