"""Finite deterministic availability analyzer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from cgt_availability.core.coherence import (
    STRICT_METADATA_KEY,
    has_declared_path_types,
    protocol_reconstructs_report_path,
    protocol_uses_legacy_reconstructs,
)
from cgt_availability.core.deficiency import Deficiency
from cgt_availability.core.dependencies import DependencyClosure, DiagnosticVocabulary
from cgt_availability.core.diagnostics import diagnostic_requires_dimension
from cgt_availability.core.package import ClaimPackage
from cgt_availability.core.pipeline import AvailabilityPipeline
from cgt_availability.core.report import AvailabilityReport
from cgt_availability.core.residual import (
    has_residual_scientific_space,
    residual_refinement_count,
    residual_repair_count,
    residual_test_count,
)
from cgt_availability.core.serialization import JSONValue
from cgt_availability.core.status import (
    AvailabilityProfile,
    AvailabilityStatus,
    coarse_availability_class,
)

CORE_MISSING_CODES = {
    "missing_frame",
    "missing_system",
    "missing_projection",
    "missing_observation",
    "missing_description",
    "missing_normalizer",
    "missing_expected_report",
    "missing_verifier",
    "missing_failure_predicate",
    "missing_reproduction_protocol",
    "missing_comparison_regime",
}

UNFORMED_CODES = {"missing_frame", "missing_system", "missing_projection"}
BLOCKING_COHERENCE_CODES = {
    "report_path_type_error",
    "verifier_failure_incoherent",
    "protocol_incoherent",
    "missing_marker_policy",
    "missing_marker_provenance",
    "marker_policy_incomplete",
    "missing_continuation_diagnostic",
    "missing_continuation",
    "marker_sensitive_missing_marker_policy",
    "continuation_sensitive_missing_continuation",
}


class AvailabilityAnalyzer:
    """Run finite deterministic diagnostics over a claim package."""

    def __init__(
        self,
        dependency_closure: DependencyClosure | None = None,
        vocabulary: DiagnosticVocabulary | None = None,
        pipeline: AvailabilityPipeline | None = None,
    ) -> None:
        if pipeline is None:
            pipeline = AvailabilityPipeline.standard(vocabulary)
        elif vocabulary is not None:
            pipeline = AvailabilityPipeline(
                name=pipeline.name,
                level=pipeline.level,
                rules=pipeline.rules,
                vocabulary=vocabulary,
                metadata=dict(pipeline.metadata),
            )
        self.pipeline = pipeline
        self.dependency_closure = dependency_closure
        self.vocabulary = pipeline.vocabulary

    @classmethod
    def default(cls) -> AvailabilityAnalyzer:
        return cls()

    def analyze(self, pkg: ClaimPackage) -> AvailabilityReport:
        analysis_pkg = self._analysis_package(pkg)
        direct_items: list[Deficiency] = []
        rule_warnings: list[str] = []
        rule_metadata: dict[str, JSONValue] = {}
        for rule in self.pipeline.rules:
            result = rule.evaluate(analysis_pkg)
            direct_items.extend(result.deficiencies)
            rule_warnings.extend(result.warnings)
            if result.metadata:
                rule_metadata[rule.name] = result.metadata

        direct = self._deduplicate(direct_items)
        dependency_closure = self.dependency_closure or DependencyClosure(
            self.vocabulary.dependency_graph, package=analysis_pkg
        )
        closed = dependency_closure.close_ordered(direct)
        profile = self._profile(analysis_pkg, closed)
        status = self._status(analysis_pkg, profile, closed)
        warnings = self._warnings(direct, closed, rule_warnings)
        recommendations = self._recommendations(closed)
        summary = self._summary(status, profile, closed)
        compatibility_warnings = self._compatibility_warnings(analysis_pkg)
        report = AvailabilityReport(
            claim_id=pkg.claim_id,
            status=status,
            profile=profile,
            deficiencies=direct,
            dependency_closed_deficiencies=closed,
            warnings=warnings,
            recommendations=recommendations,
            summary=summary,
            metadata={
                "pipeline": self.pipeline.name,
                "pipeline_level": self.pipeline.level.value,
                "pipeline_metadata": self.pipeline.metadata,
                "strict": bool(self.pipeline.metadata.get("strict", False)),
                "compatibility_warnings": compatibility_warnings,
                "diagnostic_vocabulary": self.vocabulary.name,
                "diagnostic_vocabulary_version": self.vocabulary.version,
                "rule_metadata": rule_metadata,
                "declared_components": list(analysis_pkg.declared_component_names()),
                "residual_test_count": residual_test_count(analysis_pkg),
                "residual_refinement_count": residual_refinement_count(analysis_pkg),
                "residual_repair_count": residual_repair_count(analysis_pkg),
                "has_residual_scientific_space": has_residual_scientific_space(analysis_pkg),
            },
        )
        report.metadata["coarse_availability_class"] = coarse_availability_class(report).value
        return report

    def _analysis_package(self, pkg: ClaimPackage) -> ClaimPackage:
        if not self.pipeline.metadata.get("strict", False):
            return pkg
        metadata = dict(pkg.metadata)
        metadata[STRICT_METADATA_KEY] = True
        return replace(pkg, metadata=metadata)

    def _compatibility_warnings(self, pkg: ClaimPackage) -> list[JSONValue]:
        warnings: list[JSONValue] = []
        if protocol_uses_legacy_reconstructs(pkg) and not pkg.metadata.get(STRICT_METADATA_KEY):
            warnings.append(
                {
                    "code": "legacy_reconstructs_report_path",
                    "message": (
                        "metadata['reconstructs_report_path']=True is accepted as "
                        "a v0.1 compatibility declaration; strict mode requires "
                        "ReproductionProtocolSpec.reconstructs."
                    ),
                }
            )
        return warnings

    def _profile(self, pkg: ClaimPackage, closed: tuple[Deficiency, ...]) -> AvailabilityProfile:
        closed_codes = {item.code for item in closed}
        is_complete = not bool(closed_codes & CORE_MISSING_CODES)
        is_partial = not is_complete
        is_well_typed = is_complete and has_declared_path_types(pkg) and (
            "report_path_type_error" not in closed_codes
        )
        is_blocked = any(item.severity == "blocking" for item in closed)
        coherence_blockers = closed_codes & BLOCKING_COHERENCE_CODES
        is_coherent = is_well_typed and not coherence_blockers
        is_reproducibly_available = (
            is_coherent
            and pkg.reproduction_protocol is not None
            and pkg.reproduction_protocol.declared
            and protocol_reconstructs_report_path(pkg)
            and "protocol_incoherent" not in closed_codes
        )
        is_continuation_sensitive = (
            diagnostic_requires_dimension(pkg, "continuation")
            and is_coherent
            and pkg.continuation is not None
            and pkg.continuation.declared
            and bool(pkg.continuation.diagnostic_name)
        )
        return AvailabilityProfile(
            is_partial=is_partial,
            is_complete=is_complete,
            is_well_typed=is_well_typed,
            is_coherent=is_coherent,
            is_reproducibly_available=is_reproducibly_available,
            is_continuation_sensitive=is_continuation_sensitive,
            is_blocked=is_blocked,
        )

    def _status(
        self,
        pkg: ClaimPackage,
        profile: AvailabilityProfile,
        closed: tuple[Deficiency, ...],
    ) -> AvailabilityStatus:
        closed_codes = {item.code for item in closed}
        if closed_codes & UNFORMED_CODES:
            return AvailabilityStatus.UNFORMED
        if profile.is_partial:
            return AvailabilityStatus.PARTIAL
        if closed_codes & BLOCKING_COHERENCE_CODES:
            return AvailabilityStatus.BLOCKED
        if not profile.is_well_typed:
            return AvailabilityStatus.COMPLETE
        warning_codes = {item.code for item in closed if item.severity == "warning"}
        if warning_codes:
            return AvailabilityStatus.WELL_TYPED
        if profile.is_continuation_sensitive:
            return AvailabilityStatus.CONTINUATION_SENSITIVE
        if profile.is_reproducibly_available:
            return AvailabilityStatus.REPRODUCIBLY_AVAILABLE
        if profile.is_coherent:
            return AvailabilityStatus.COHERENT
        return AvailabilityStatus.BLOCKED

    def _warnings(
        self,
        direct: tuple[Deficiency, ...],
        closed: tuple[Deficiency, ...],
        rule_warnings: Iterable[str],
    ) -> tuple[str, ...]:
        messages = [item.message for item in (*direct, *closed) if item.severity == "warning"]
        messages.extend(rule_warnings)
        return tuple(dict.fromkeys(messages))

    def _recommendations(self, closed: tuple[Deficiency, ...]) -> tuple[str, ...]:
        recommendations: list[str] = []
        for deficiency in closed:
            recommendations.append(_recommendation_for(deficiency))
        return tuple(dict.fromkeys(recommendations))

    def _summary(
        self,
        status: AvailabilityStatus,
        profile: AvailabilityProfile,
        closed: tuple[Deficiency, ...],
    ) -> str:
        blocking = sum(1 for item in closed if item.severity == "blocking")
        warnings = sum(1 for item in closed if item.severity == "warning")
        return (
            f"Package is {status.value}; dependency-closed profile contains "
            f"{blocking} blocking deficiencies and {warnings} warnings. "
            f"Layered profile: complete={profile.is_complete}, "
            f"well_typed={profile.is_well_typed}, coherent={profile.is_coherent}, "
            f"reproducible={profile.is_reproducibly_available}."
        )

    def _deduplicate(self, deficiencies: Iterable[Deficiency]) -> tuple[Deficiency, ...]:
        by_key: dict[tuple[str, str], Deficiency] = {}
        for deficiency in deficiencies:
            key = (deficiency.code, str(deficiency.metadata.get("dimension", "")))
            if key not in by_key:
                by_key[key] = deficiency
        return tuple(sorted(by_key.values(), key=lambda item: item.sort_key()))


def _recommendation_for(deficiency: Deficiency) -> str:
    recommendations = {
        "missing_frame": "Declare the CGT frame in which the selected effects are interpreted.",
        "missing_system": "Declare the system or constraint package that produces the claim.",
        "missing_projection": (
            "Declare the selected effect projection before observation or verification."
        ),
        "missing_observation": "Declare an observation constraint for the selected projection.",
        "missing_description": "Declare a description format for observed effects.",
        "missing_normalizer": "Declare a normalizer for comparable reports.",
        "missing_expected_report": "Declare the expected report class or target report region.",
        "missing_verifier": "Declare the finite verifier and its verdict domain.",
        "missing_failure_predicate": "Declare an operational failure predicate.",
        "missing_reproduction_protocol": "Declare a reproduction protocol for the report path.",
        "missing_comparison_regime": "Declare the comparison regime used by the comparative claim.",
        "missing_provenance": (
            "Add provenance references for data, code, protocol, or source material."
        ),
        "missing_history": (
            "Declare construction history if history-sensitive diagnosis is requested."
        ),
        "missing_marker_policy": (
            "Declare a marker or inconsistency policy for marker-sensitive diagnosis."
        ),
        "missing_marker_provenance": (
            "Declare provenance for marker-generating or marker-preserving constraints."
        ),
        "marker_policy_incomplete": (
            "State whether unresolved markers are tracked and preserved."
        ),
        "missing_continuation": "Declare residual constraints or follow-up structure.",
        "missing_continuation_diagnostic": (
            "Declare the residual diagnostic used to read continuation data."
        ),
        "verifier_failure_incoherent": (
            "Align the failure predicate with the verifier's fail verdict."
        ),
        "report_path_type_error": "Repair report-path domain and codomain metadata.",
        "protocol_incoherent": "Make the protocol reconstruct the selected report path.",
        "direct_selector_degeneracy_risk": (
            "Add selector-language, history, cost, locality, or effect-profile controls."
        ),
        "report_only_insufficiency_risk": (
            "Include omitted diagnostic dimensions or avoid report-only diagnosis for them."
        ),
        "marker_sensitive_missing_marker_policy": (
            "Provide marker policy before marker-sensitive use."
        ),
        "continuation_sensitive_missing_continuation": (
            "Provide continuation data before continuation-sensitive use."
        ),
    }
    return recommendations.get(deficiency.code, f"Address deficiency {deficiency.code}.")
