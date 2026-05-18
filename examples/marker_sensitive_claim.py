from dataclasses import replace

from cgt_availability import (
    AvailabilityAnalyzer,
    ClaimPackage,
    DescriptionSpec,
    ExpectedReportSpec,
    FailurePredicateSpec,
    FrameSpec,
    MarkerPolicySpec,
    NormalizerSpec,
    ObservationSpec,
    ProjectionSpec,
    ProvenanceRef,
    ReproductionProtocolSpec,
    SystemSpec,
    VerifierSpec,
    render_markdown_report,
)


def base_package() -> ClaimPackage:
    return ClaimPackage(
        claim_id="marker-sensitive-missing-policy",
        statement="The normalized report is clean after resolving source conflicts.",
        frame=FrameSpec(id="marker-frame"),
        system=SystemSpec(id="conflict-normalization-system"),
        projection=ProjectionSpec(
            id="clean-report",
            metadata={
                "domain": "effect_profile",
                "codomain": "selected_effect",
                "omits_dimensions": ["marker"],
            },
        ),
        observation=ObservationSpec(
            id="observe",
            metadata={"domain": "selected_effect", "codomain": "observation"},
        ),
        description=DescriptionSpec(
            id="describe",
            metadata={"domain": "observation", "codomain": "description"},
        ),
        normalizer=NormalizerSpec(
            id="normalize",
            metadata={"domain": "description", "codomain": "report"},
        ),
        expected_report=ExpectedReportSpec(id="expected-clean"),
        verifier=VerifierSpec(id="verifier"),
        failure_predicate=FailurePredicateSpec(id="failure"),
        reproduction_protocol=ReproductionProtocolSpec(
            id="protocol",
            metadata={"reconstructs_report_path": True},
        ),
        provenance=(ProvenanceRef(id="example"),),
        metadata={"marker_sensitive": True},
    )


def main() -> None:
    analyzer = AvailabilityAnalyzer.default()
    missing = base_package()
    fixed = replace(
        missing,
        claim_id="marker-sensitive-with-policy",
        marker_policy=MarkerPolicySpec(
            id="preserve-open-markers",
            tracks_unresolved=True,
            marker_provenance=("source-conflict-log",),
            preserves_markers=True,
        ),
    )
    for pkg in (missing, fixed):
        print(render_markdown_report(analyzer.analyze(pkg)))


if __name__ == "__main__":
    main()
