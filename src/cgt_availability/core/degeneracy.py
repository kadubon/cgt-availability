"""Finite witnesses for direct-selector degeneracy diagnostics."""

from __future__ import annotations

from dataclasses import dataclass

from cgt_availability.core.package import ClaimPackage
from cgt_availability.core.serialization import JSONValue, ensure_json_object


@dataclass(frozen=True)
class DirectSelectorWitness:
    """Witness that structured and direct-coded packages are diagnostically equivalent."""

    structured_id: str
    direct_id: str
    report: JSONValue
    verifier_verdict: str
    missing_controls: tuple[str, ...]
    explanation: str = (
        "The packages share report and verdict while no declared degeneracy controls "
        "separate structured construction from direct target coding."
    )

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


def direct_selector_witness(
    pkg: ClaimPackage,
    *,
    structured_id: str = "structured",
    direct_id: str = "direct_selector",
    report: JSONValue = "same_report",
    verifier_verdict: str = "pass",
) -> DirectSelectorWitness | None:
    """Return a finite degeneracy witness when selector controls are absent."""
    selector_relevant = (
        bool(pkg.metadata.get("direct_selector_regime", False))
        or bool(pkg.metadata.get("unrestricted_selector_regime", False))
        or (
            pkg.history is not None
            and pkg.history.construction_kind == "direct_selector"
        )
    )
    if not selector_relevant:
        return None
    control = pkg.degeneracy_control
    if control is not None and (
        control.restricted_selector_language or bool(control.controls)
    ):
        return None
    return DirectSelectorWitness(
        structured_id=structured_id,
        direct_id=direct_id,
        report=report,
        verifier_verdict=verifier_verdict,
        missing_controls=(
            "history",
            "cost",
            "locality",
            "effect_profile",
            "selector_language",
        ),
    )
