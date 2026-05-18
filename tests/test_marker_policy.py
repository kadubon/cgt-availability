from dataclasses import replace

from cgt_availability import AvailabilityAnalyzer, MarkerPolicySpec, ProjectionSpec


def test_marker_sensitive_policy_requires_provenance(complete_package) -> None:  # type: ignore[no-untyped-def]
    pkg = replace(
        complete_package,
        marker_policy=MarkerPolicySpec(
            id="marker-policy",
            tracks_unresolved=True,
            preserves_markers=True,
        ),
        metadata={"marker_sensitive": True},
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert "missing_marker_provenance" in {item.code for item in report.deficiencies}
    assert report.profile.is_blocked


def test_marker_policy_incomplete_blocks_marker_sensitive_coherence(complete_package) -> None:  # type: ignore[no-untyped-def]
    pkg = replace(
        complete_package,
        marker_policy=MarkerPolicySpec(
            id="marker-policy",
            marker_provenance=("conflict-log",),
        ),
        metadata={"marker_sensitive": True},
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    deficiency = next(
        item for item in report.deficiencies if item.code == "marker_policy_incomplete"
    )
    assert deficiency.severity == "blocking"
    assert not report.profile.is_coherent
    assert not report.profile.is_reproducibly_available


def test_marker_sensitive_report_insufficiency_with_complete_policy(complete_package) -> None:  # type: ignore[no-untyped-def]
    pkg = replace(
        complete_package,
        projection=ProjectionSpec(
            id="projection",
            metadata={
                "domain": "effect_profile",
                "codomain": "projected",
                "omits_dimensions": ["marker"],
            },
        ),
        marker_policy=MarkerPolicySpec(
            id="marker-policy",
            tracks_unresolved=True,
            marker_provenance=("conflict-log",),
            preserves_markers=True,
        ),
        metadata={"marker_sensitive": True},
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert "report_only_insufficiency_risk" in {item.code for item in report.deficiencies}
    assert "missing_marker_provenance" not in {item.code for item in report.deficiencies}
