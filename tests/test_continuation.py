from dataclasses import replace

from cgt_availability import (
    AvailabilityAnalyzer,
    AvailabilityStatus,
    ContinuationSpec,
    ResidualTransitionSystem,
    has_residual_simulation,
    one_step_residual_labels,
    residual_includes,
    residual_refinement_count,
    residual_repair_count,
    residual_test_count,
)


def test_continuation_counts_follow_up_tests(complete_package) -> None:  # type: ignore[no-untyped-def]
    pkg = replace(
        complete_package,
        continuation=ContinuationSpec(
            id="continuation",
            residual_constraints=("probe",),
            follow_up_tests=("probe", "replication"),
            refinement_paths=("refine",),
            repair_paths=("repair",),
            diagnostic_name="follow_up_test_count",
        ),
        metadata={"continuation_sensitive": True},
    )
    assert residual_test_count(pkg) == 2
    assert residual_refinement_count(pkg) == 1
    assert residual_repair_count(pkg) == 1
    status = AvailabilityAnalyzer.default().analyze(pkg).status
    assert status == AvailabilityStatus.CONTINUATION_SENSITIVE


def test_continuation_sensitive_requires_diagnostic_name(complete_package) -> None:  # type: ignore[no-untyped-def]
    pkg = replace(
        complete_package,
        continuation=ContinuationSpec(id="continuation", residual_constraints=("probe",)),
        metadata={"continuation_sensitive": True},
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert "missing_continuation_diagnostic" in {item.code for item in report.deficiencies}
    assert report.profile.is_blocked


def test_empty_continuation_warns(complete_package) -> None:  # type: ignore[no-untyped-def]
    pkg = replace(complete_package, continuation=ContinuationSpec(id="continuation"))
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert any("Continuation is declared" in warning for warning in report.warnings)


def test_one_step_residual_transition_helpers() -> None:
    smaller = ResidualTransitionSystem(
        states=("root", "s1"),
        root="root",
        transitions=(("root", "probe", "s1"),),
    )
    larger = ResidualTransitionSystem(
        states=("root", "s1", "s2"),
        root="root",
        transitions=(("root", "probe", "s1"), ("root", "repair", "s2")),
    )
    assert one_step_residual_labels(larger) == ("probe", "repair")
    assert residual_includes(larger, smaller)
    assert has_residual_simulation(smaller, larger)
