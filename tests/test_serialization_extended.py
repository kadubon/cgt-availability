from cgt_availability import (
    ClaimPackage,
    ComparisonRegimeSpec,
    ContinuationSpec,
    MarkerPolicySpec,
    ReportPathSpec,
    ResidualConstraintSpec,
    TypedMapSpec,
)


def test_extended_claim_package_json_roundtrip() -> None:
    pkg = ClaimPackage(
        claim_id="extended",
        statement="Extended package.",
        comparison_regime=ComparisonRegimeSpec(id="comparison", dimensions=("score",)),
        report_path=ReportPathSpec(
            id="path",
            projection=TypedMapSpec(id="p", domain="effect", codomain="projected"),
            observation=TypedMapSpec(id="o", domain="projected", codomain="observed"),
            description_map=TypedMapSpec(id="d", domain="observed", codomain="described"),
            normalizer=TypedMapSpec(id="n", domain="described", codomain="report"),
        ),
        continuation=ContinuationSpec(
            id="continuation",
            diagnostic_name="residual_count",
            residual_constraint_specs=(
                ResidualConstraintSpec(
                    id="probe",
                    constraint_type="follow_up_test",
                    effect_dimensions=("continuation",),
                ),
            ),
        ),
        marker_policy=MarkerPolicySpec(
            id="marker",
            tracks_unresolved=True,
            marker_provenance=("log",),
            preserves_markers=True,
        ),
    )
    restored = ClaimPackage.from_json(pkg.to_json())
    assert restored.comparison_regime is not None
    assert restored.report_path is not None
    assert restored.continuation is not None
    assert restored.continuation.residual_constraint_specs[0].constraint_type == "follow_up_test"
    assert restored.marker_policy is not None
    assert restored.marker_policy.preserves_markers
