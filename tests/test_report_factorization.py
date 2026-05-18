from dataclasses import replace

from cgt_availability import AvailabilityAnalyzer, ProjectionSpec


def test_projection_omitting_continuation_warns_when_requested(complete_package) -> None:  # type: ignore[no-untyped-def]
    pkg = replace(
        complete_package,
        projection=ProjectionSpec(
            id="projection",
            metadata={
                "domain": "effect_profile",
                "codomain": "projected",
                "omits_dimensions": ["continuation"],
            },
        ),
        metadata={"continuation_sensitive": True},
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert "report_only_insufficiency_risk" in {item.code for item in report.deficiencies}
    assert "missing_continuation" in {item.code for item in report.deficiencies}


def test_projection_omitting_marker_warns_when_requested(complete_package) -> None:  # type: ignore[no-untyped-def]
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
        metadata={"marker_sensitive": True},
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert "report_only_insufficiency_risk" in {item.code for item in report.deficiencies}
    assert "missing_marker_policy" in {item.code for item in report.deficiencies}
