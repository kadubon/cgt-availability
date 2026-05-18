"""Theory-alignment records for documentation and tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from cgt_availability.core.serialization import JSONValue, ensure_json_object


class TheoryImplementationStatus(StrEnum):
    """Implementation status for one paper concept."""

    IMPLEMENTED = "implemented"
    POC_APPROXIMATION = "poc_approximation"
    ADAPTER_BOUNDARY = "adapter_boundary"
    NOT_IMPLEMENTED = "not_implemented"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass(frozen=True)
class TheoryAlignmentItem:
    """One mapping from a paper concept to repository implementation."""

    concept: str
    paper_location: str
    status: TheoryImplementationStatus
    implementation: str
    notes: str = ""

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class TheoryAlignmentReport:
    """Non-runtime audit artifact describing theory-to-code alignment."""

    title: str
    items: tuple[TheoryAlignmentItem, ...]
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


def default_theory_alignment_report() -> TheoryAlignmentReport:
    """Return the maintained theory alignment table."""
    return TheoryAlignmentReport(
        title="CGT scientific availability theory alignment",
        items=(
            TheoryAlignmentItem(
                "partial scientific availability package",
                "TeX:182 Partial scientific availability package",
                TheoryImplementationStatus.IMPLEMENTED,
                "cgt_availability.ClaimPackage and spec dataclasses",
            ),
            TheoryAlignmentItem(
                "continuation-extended package",
                "TeX:205 Continuation-extended package",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "ContinuationSpec and residual helpers",
                "The implementation handles finite declared residual structures only.",
            ),
            TheoryAlignmentItem(
                "complete package",
                "TeX:213 Complete package",
                TheoryImplementationStatus.IMPLEMENTED,
                "AvailabilityProfile.is_complete and required component rules",
            ),
            TheoryAlignmentItem(
                "report path",
                "TeX:221 Report path",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "ReportPathSpec, TypedMapSpec, and legacy metadata compatibility",
                "Checks finite declarations rather than semantic functions.",
            ),
            TheoryAlignmentItem(
                "well-typed package",
                "TeX:242 Well-typed package",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "report-path and report-consumer domain/codomain checks",
                "Checks declared string labels, not mathematical domains.",
            ),
            TheoryAlignmentItem(
                "coherence components",
                "TeX:265 Coherence components",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "rule pack for path, verifier/failure, protocol, degeneracy, marker, continuation",
                "Finite rule checks only; no theorem proving.",
            ),
            TheoryAlignmentItem(
                "coherent package",
                "TeX:284 Coherent package",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "AvailabilityProfile.is_coherent",
                "Coherence follows implemented finite rules and declared diagnostics.",
            ),
            TheoryAlignmentItem(
                "reproducibly available package",
                "TeX:288 Reproducibly available package",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "ReproductionProtocolSpec.reconstructs and profile.is_reproducibly_available",
                "Strict mode requires explicit finite report-path replay declarations.",
            ),
            TheoryAlignmentItem(
                "availability is not verifier success",
                "TeX:292 Availability is not verdict success",
                TheoryImplementationStatus.IMPLEMENTED,
                "separate AvailabilityProfile and verifier readout helpers",
            ),
            TheoryAlignmentItem(
                "truth is not the diagnostic target",
                "TeX:296 Truth is not the diagnostic target",
                TheoryImplementationStatus.OUT_OF_SCOPE,
                "explicit non-goal in README, docs, and adapters",
            ),
            TheoryAlignmentItem(
                "primitive deficiency symbols",
                "TeX:302 Primitive deficiency symbols",
                TheoryImplementationStatus.IMPLEMENTED,
                "DeficiencyCode and DEFICIENCY_CODE_INFO",
            ),
            TheoryAlignmentItem(
                "direct deficiency profile",
                "TeX:324 Direct deficiency profile",
                TheoryImplementationStatus.IMPLEMENTED,
                "AvailabilityReport.deficiencies",
            ),
            TheoryAlignmentItem(
                "package-relative dependency relation",
                "TeX:328 Package-relative dependency relation on deficiencies",
                TheoryImplementationStatus.IMPLEMENTED,
                "DependencyGraph, DependencyEdge, DependencyCondition",
                "Current graph is finite and deterministic.",
            ),
            TheoryAlignmentItem(
                "dependency-closed deficiency profile",
                "TeX:354 Dependency-closed deficiency profile",
                TheoryImplementationStatus.IMPLEMENTED,
                "DependencyGraph, DependencyClosure, DiagnosticVocabulary",
            ),
            TheoryAlignmentItem(
                "availability preorder",
                "TeX:403 Availability preorder",
                TheoryImplementationStatus.IMPLEMENTED,
                "availability_preorder over dependency-closed profiles",
            ),
            TheoryAlignmentItem(
                "coarse availability labels",
                "TeX:431 Coarse availability labels",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "CoarseAvailabilityClass",
                "Lossy secondary summaries, not primary diagnostic objects.",
            ),
            TheoryAlignmentItem(
                "compatible non-destructive completion",
                "TeX:459 Compatible non-destructive completion",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "PackagePatch and CoherentRepairProblem",
                "Finite patch search only; no arbitrary synthesis.",
            ),
            TheoryAlignmentItem(
                "report-factorization obstruction",
                "TeX:575 Report-factorization obstruction",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "FactorizationWitness and projection omitted-dimension diagnostics",
                "Witnesses finite samples rather than symbolic factorization.",
            ),
            TheoryAlignmentItem(
                "history-sensitive diagnostic",
                "TeX:603 History-sensitive diagnostic",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "history metadata, report omission checks, direct-selector diagnostics",
            ),
            TheoryAlignmentItem(
                "residual constraint space",
                "TeX:627 Residual constraint space",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "ContinuationSpec and ResidualConstraintSpec",
            ),
            TheoryAlignmentItem(
                "residual transition system",
                "TeX:650 Residual transition system",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "ResidualTransitionSystem with finite validation",
            ),
            TheoryAlignmentItem(
                "residual simulation",
                "TeX:658 Residual simulation",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "bounded_residual_simulation",
                "Bounded label simulation only.",
            ),
            TheoryAlignmentItem(
                "continuation-sensitive diagnostic",
                "TeX:666 Continuation-sensitive diagnostic",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "ContinuationSpec, ResidualTransitionSystem, bounded simulation",
            ),
            TheoryAlignmentItem(
                "continuation diagnostic preorder",
                "TeX:700 Continuation diagnostic preorder",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "continuation_preorder and continuation_preorder_result",
            ),
            TheoryAlignmentItem(
                "marker-sensitive diagnostic",
                "TeX:746 Marker-sensitive diagnostic",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "MarkerPolicySpec and MarkerStateSpec",
            ),
            TheoryAlignmentItem(
                "direct-selector degeneracy",
                "TeX:762 Direct-selector degeneracy",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "Degeneracy checks and DirectSelectorWitness",
            ),
            TheoryAlignmentItem(
                "deficiency repair cover",
                "TeX:786 Deficiency Repair Cover",
                TheoryImplementationStatus.IMPLEMENTED,
                "solve_repair_cover and greedy_repair_cover",
                "Finite exact/greedy algorithms only.",
            ),
            TheoryAlignmentItem(
                "conflict-constrained repair",
                "TeX:819 Conflict-constrained repair",
                TheoryImplementationStatus.IMPLEMENTED,
                "RepairCandidate.conflicts_with and solver filtering",
            ),
            TheoryAlignmentItem(
                "continuation-sensitive completion",
                "TeX:839 Continuation-sensitive completion",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "ContinuationRepairProblem",
                "Finite residual-effect threshold and declared diagnostic names only.",
            ),
            TheoryAlignmentItem(
                "cascaded availability completion",
                "TeX:859 Cascaded availability completion",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "solve_cascaded_repair",
                "Finite ordered prerequisite search only.",
            ),
            TheoryAlignmentItem(
                "deficiency lattice and infinitary dependency operator",
                "TeX:872 Deficiency lattice and infinitary dependency operator",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "least_fixed_point finite Kleene iteration over deficiency codes",
                "Finite powerset-style operators only.",
            ),
            TheoryAlignmentItem(
                "transfinite deficiency iteration",
                "TeX:892 Transfinite deficiency iteration",
                TheoryImplementationStatus.NOT_IMPLEMENTED,
                "documented non-claim",
                "No ordinal engine is implemented.",
            ),
            TheoryAlignmentItem(
                "nondeterministic may/must/almost-sure availability",
                "TeX:919 Nondeterministic availability modes",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "evaluate_run_modes and almost_sure_available over finite run families",
                "Almost-sure mode requires explicit finite probabilities.",
            ),
            TheoryAlignmentItem(
                "coinductive availability",
                "TeX:936 Coinductive availability, schematic",
                TheoryImplementationStatus.NOT_IMPLEMENTED,
                "documented roadmap item",
                "No stream-level coinductive semantics are implemented.",
            ),
            TheoryAlignmentItem(
                "finite probabilistic availability model readout",
                "TeX:868 Infinitary and nondeterministic availability",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "FiniteDTMC with bounded and unbounded reachability probability",
                "This is finite DTMC reachability, not full temporal-logic model checking.",
            ),
            TheoryAlignmentItem(
                "finite statistical verifier readout",
                "TeX:156 Relation to statistics and model checking",
                TheoryImplementationStatus.POC_APPROXIMATION,
                "BernoulliEvidence and evaluate_binomial_verifier",
                "Statistical significance is reported as a declared verifier readout, not truth.",
            ),
            TheoryAlignmentItem(
                "external statistical and model-checking tools",
                "TeX:983 Relation to philosophy of science and reproducibility",
                TheoryImplementationStatus.ADAPTER_BOUNDARY,
                "cgt_availability.adapters optional integration points",
                "Adapters are explicit tool boundaries and not core truth judgments.",
            ),
        ),
        metadata={"runtime_judgment": False},
    )
