from dataclasses import replace

from conftest import make_complete_package

from cgt_availability import (
    AvailabilityAnalyzer,
    AvailabilityPipeline,
    AvailabilityStatus,
    ClaimPackage,
    ComparisonRegimeSpec,
    DegeneracyControlSpec,
    HistorySpec,
    ReportPathSpec,
    TypedMapSpec,
)


def test_empty_minimal_package_returns_missing_core_deficiencies() -> None:
    report = AvailabilityAnalyzer.default().analyze(ClaimPackage("minimal", "A bare claim."))
    codes = {item.code for item in report.dependency_closed_deficiencies}
    assert report.status == AvailabilityStatus.UNFORMED
    assert "missing_frame" in codes
    assert "missing_projection" in codes
    assert "missing_verifier" in codes


def test_vague_claim_has_core_missing_diagnostics() -> None:
    pkg = ClaimPackage(
        claim_id="vague",
        statement="This AI is smarter than humans.",
        metadata={"comparison_required": True},
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    codes = {item.code for item in report.dependency_closed_deficiencies}
    assert "missing_comparison_regime" in codes
    assert "missing_observation" in codes
    assert "missing_failure_predicate" in codes
    assert "missing_reproduction_protocol" in codes


def test_complete_package_is_reproducibly_available(complete_package) -> None:  # type: ignore[no-untyped-def]
    report = AvailabilityAnalyzer.default().analyze(complete_package)
    assert report.status == AvailabilityStatus.REPRODUCIBLY_AVAILABLE
    assert report.profile.is_complete
    assert report.profile.is_well_typed
    assert report.profile.is_coherent
    assert report.profile.is_reproducibly_available
    assert not [item for item in report.deficiencies if item.severity == "blocking"]
    assert report.metadata["compatibility_warnings"]


def test_strict_pipeline_does_not_accept_legacy_protocol_metadata(
    complete_package,
) -> None:  # type: ignore[no-untyped-def]
    pipeline = AvailabilityPipeline.standard()
    pipeline = AvailabilityPipeline(
        name=pipeline.name,
        level=pipeline.level,
        rules=pipeline.rules,
        vocabulary=pipeline.vocabulary,
        metadata={**pipeline.metadata, "strict": True},
    )

    report = AvailabilityAnalyzer(pipeline=pipeline).analyze(complete_package)

    assert "protocol_incoherent" in {item.code for item in report.deficiencies}
    assert not report.profile.is_reproducibly_available


def test_first_class_comparison_regime_satisfies_comparison_requirement() -> None:
    pkg = make_complete_package(
        comparison_regime=ComparisonRegimeSpec(
            id="comparison",
            dimensions=("accuracy",),
            relation="greater_or_equal",
        ),
        metadata={"comparison_required": True},
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert "missing_comparison_regime" not in {item.code for item in report.deficiencies}


def test_typed_report_path_takes_precedence_over_metadata_path() -> None:
    pkg = make_complete_package(
        report_path=ReportPathSpec(
            id="typed-report-path",
            projection=TypedMapSpec(id="p", domain="effect_profile", codomain="p"),
            observation=TypedMapSpec(id="o", domain="p", codomain="o"),
            description_map=TypedMapSpec(id="d", domain="o", codomain="d"),
            normalizer=TypedMapSpec(id="n", domain="d", codomain="report"),
        )
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert "report_path_type_error" not in {item.code for item in report.deficiencies}


def test_bad_typed_report_path_is_detected() -> None:
    pkg = make_complete_package(
        report_path=ReportPathSpec(
            id="typed-report-path",
            projection=TypedMapSpec(id="p", domain="effect_profile", codomain="p"),
            observation=TypedMapSpec(id="o", domain="wrong", codomain="o"),
            description_map=TypedMapSpec(id="d", domain="o", codomain="d"),
            normalizer=TypedMapSpec(id="n", domain="d", codomain="report"),
        )
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert "report_path_type_error" in {item.code for item in report.deficiencies}


def test_direct_selector_without_controls_is_flagged(complete_package) -> None:  # type: ignore[no-untyped-def]
    pkg = replace(
        complete_package,
        history=HistorySpec(id="history", construction_kind="direct_selector"),
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert "direct_selector_degeneracy_risk" in {item.code for item in report.deficiencies}


def test_direct_selector_with_control_reduces_degeneracy_warning(complete_package) -> None:  # type: ignore[no-untyped-def]
    pkg = replace(
        complete_package,
        history=HistorySpec(id="history", construction_kind="direct_selector"),
        degeneracy_control=DegeneracyControlSpec(id="control", controls=("history",)),
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert "direct_selector_degeneracy_risk" not in {item.code for item in report.deficiencies}


def test_benchmark_like_package_can_be_well_typed_with_report_warning() -> None:
    pkg = make_complete_package(
        claim_id="benchmark",
        statement="Model M gets 90% on benchmark B.",
        projection=make_complete_package().projection.__class__(  # type: ignore[union-attr]
            id="projection",
            metadata={
                "domain": "effect_profile",
                "codomain": "projected",
                "omits_dimensions": ["calibration"],
            },
        ),
        metadata={"diagnostics_requested": ["calibration"]},
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert report.status == AvailabilityStatus.WELL_TYPED
    assert "report_only_insufficiency_risk" in {item.code for item in report.deficiencies}
