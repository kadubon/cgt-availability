from cgt_availability import (
    AvailabilityAnalyzer,
    ClaimPackage,
    DescriptionSpec,
    ExpectedReportSpec,
    FailurePredicateSpec,
    FrameSpec,
    NormalizerSpec,
    ObservationSpec,
    ProjectionSpec,
    ProvenanceRef,
    ReproductionProtocolSpec,
    SystemSpec,
    VerifierSpec,
    render_markdown_report,
)


def main() -> None:
    pkg = ClaimPackage(
        claim_id="benchmark-claim",
        statement="Model M gets 90% on benchmark B.",
        frame=FrameSpec(
            id="ml-benchmark-frame",
            metadata={"comparison_regime": "accuracy-threshold"},
        ),
        system=SystemSpec(id="model-m-on-benchmark-b"),
        projection=ProjectionSpec(
            id="accuracy",
            metadata={
                "domain": "effect_profile",
                "codomain": "benchmark_run",
                "omits_dimensions": ["calibration", "variance", "leakage"],
            },
        ),
        observation=ObservationSpec(
            id="benchmark-execution",
            metadata={"domain": "benchmark_run", "codomain": "score_file"},
        ),
        description=DescriptionSpec(
            id="score-json",
            metadata={"domain": "score_file", "codomain": "score_record"},
        ),
        normalizer=NormalizerSpec(
            id="accuracy-normalizer",
            metadata={"domain": "score_record", "codomain": "normalized_accuracy"},
        ),
        expected_report=ExpectedReportSpec(id="at-least-0.90"),
        verifier=VerifierSpec(id="threshold-verifier", rule="accuracy >= 0.90"),
        failure_predicate=FailurePredicateSpec(id="threshold-failure", rule="accuracy < 0.90"),
        reproduction_protocol=ReproductionProtocolSpec(
            id="benchmark-protocol",
            metadata={
                "reconstructs_report_path": True,
                "references": [
                    "projection",
                    "observation",
                    "description",
                    "normalizer",
                    "verifier",
                ],
            },
        ),
        provenance=(
            ProvenanceRef(id="benchmark-card", uri="https://example.invalid/benchmark-card"),
        ),
        metadata={
            "comparison_required": True,
            "diagnostics_requested": ["calibration", "variance", "leakage"],
        },
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    print(render_markdown_report(report))


if __name__ == "__main__":
    main()
