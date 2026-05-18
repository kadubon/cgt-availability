"""Direct-selector degeneracy checks."""

from __future__ import annotations

from cgt_availability.core.deficiency import Deficiency, make_deficiency
from cgt_availability.core.package import ClaimPackage

DEGENERACY_CONTROLS = {
    "history",
    "cost",
    "locality",
    "effect_profile",
    "selector_language",
    "description_length",
    "marginal_effect",
}


def find_degeneracy_deficiencies(pkg: ClaimPackage) -> tuple[Deficiency, ...]:
    if not direct_selector_relevant(pkg):
        return ()
    control = pkg.degeneracy_control
    if control is None or not control.declared:
        return (make_deficiency("direct_selector_degeneracy_risk"),)
    declared_controls = set(control.controls)
    if control.restricted_selector_language:
        return ()
    if not declared_controls & DEGENERACY_CONTROLS:
        return (
            make_deficiency(
                "direct_selector_degeneracy_risk",
                message=(
                    "A direct or unrestricted selector regime is declared without history, cost, "
                    "locality, effect-profile, selector-language, or description-length controls."
                ),
            ),
        )
    return ()


def direct_selector_relevant(pkg: ClaimPackage) -> bool:
    if bool(pkg.metadata.get("direct_selector_regime", False)):
        return True
    if bool(pkg.metadata.get("unrestricted_selector_regime", False)):
        return True
    if pkg.history is None:
        return False
    return pkg.history.construction_kind == "direct_selector"
