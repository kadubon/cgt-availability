"""Verifier/failure and protocol coherence checks."""

from __future__ import annotations

from cgt_availability.core.coherence import (
    protocol_missing_reconstructed_components,
    protocol_references_unknown_components,
    verifier_failure_contradiction,
)
from cgt_availability.core.deficiency import Deficiency, make_deficiency
from cgt_availability.core.package import ClaimPackage


def find_coherence_deficiencies(pkg: ClaimPackage) -> tuple[Deficiency, ...]:
    deficiencies: list[Deficiency] = []

    if verifier_failure_contradiction(pkg):
        deficiencies.append(make_deficiency("verifier_failure_incoherent"))

    protocol = pkg.reproduction_protocol
    if protocol is not None and protocol.metadata.get("reconstructs_report_path") is False:
        deficiencies.append(make_deficiency("protocol_incoherent"))

    missing_reconstructs = protocol_missing_reconstructed_components(pkg)
    if missing_reconstructs:
        deficiencies.append(
            make_deficiency(
                "protocol_incoherent",
                message=(
                    "The reproduction protocol does not reconstruct all "
                    "report-path components."
                ),
                metadata={"missing_components": list(missing_reconstructs)},
            )
        )

    unknown = protocol_references_unknown_components(pkg)
    if unknown:
        deficiencies.append(
            make_deficiency(
                "protocol_incoherent",
                severity="warning",
                message="The reproduction protocol references unknown components.",
                metadata={"unknown_components": list(unknown)},
            )
        )

    return tuple(deficiencies)
