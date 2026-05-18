from cgt_availability import (
    AvailabilityAnalyzer,
    ClaimPackage,
    ContinuationSpec,
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
    residual_test_count,
)


def package_with_continuation(claim_id: str, follow_up_tests: tuple[str, ...]) -> ClaimPackage:
    return ClaimPackage(
        claim_id=claim_id,
        statement="Model M passes threshold T with normalized report pass.",
        frame=FrameSpec(id="frame"),
        system=SystemSpec(id=f"system-{claim_id}"),
        projection=ProjectionSpec(
            id="pass-report",
            metadata={
                "domain": "effect_profile",
                "codomain": "selected_effect",
                "omits_dimensions": ["continuation"],
            },
        ),
        observation=ObservationSpec(
            id="observe-pass",
            metadata={"domain": "selected_effect", "codomain": "observation"},
        ),
        description=DescriptionSpec(
            id="describe-pass",
            metadata={"domain": "observation", "codomain": "description"},
        ),
        normalizer=NormalizerSpec(
            id="normalize-pass",
            metadata={"domain": "description", "codomain": "report"},
        ),
        expected_report=ExpectedReportSpec(id="expected-pass"),
        verifier=VerifierSpec(id="verifier"),
        failure_predicate=FailurePredicateSpec(id="failure"),
        reproduction_protocol=ReproductionProtocolSpec(
            id="protocol",
            metadata={"reconstructs_report_path": True},
        ),
        continuation=ContinuationSpec(
            id=f"continuation-{claim_id}",
            residual_constraints=follow_up_tests,
            follow_up_tests=follow_up_tests,
            diagnostic_name="follow_up_test_count",
        ),
        provenance=(ProvenanceRef(id="example"),),
        metadata={"continuation_sensitive": True},
    )


def main() -> None:
    analyzer = AvailabilityAnalyzer.default()
    richer = package_with_continuation("same-report-richer-continuation", ("calibration-probe",))
    closed = package_with_continuation("same-report-closed-continuation", ())
    for pkg in (richer, closed):
        report = analyzer.analyze(pkg)
        print(render_markdown_report(report))
        print(f"Residual follow-up tests: {residual_test_count(pkg)}")


if __name__ == "__main__":
    main()
