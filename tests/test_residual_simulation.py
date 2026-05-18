from conftest import make_complete_package

from cgt_availability import (
    ContinuationSpec,
    ResidualComparisonSpec,
    ResidualConstraintSpec,
    ResidualTransitionSystem,
    bounded_residual_simulation,
    continuation_preorder,
    continuation_preorder_result,
    continuation_readout,
)


def test_bounded_residual_simulation_matches_label_inclusion() -> None:
    source = ResidualTransitionSystem(
        states=("s0", "s1"),
        root="s0",
        transitions=(("s0", "follow_up", "s1"),),
    )
    target = ResidualTransitionSystem(
        states=("t0", "t1", "t2"),
        root="t0",
        transitions=(("t0", "follow_up", "t1"), ("t0", "repair", "t2")),
    )

    result = bounded_residual_simulation(source, target, max_depth=1)

    assert result.matched
    assert result.missing == ()


def test_bounded_residual_simulation_reports_missing_labels() -> None:
    source = ResidualTransitionSystem(
        states=("s0", "s1"),
        root="s0",
        transitions=(("s0", "unmatched", "s1"),),
    )
    target = ResidualTransitionSystem(states=("t0",), root="t0")

    result = bounded_residual_simulation(source, target, max_depth=1)

    assert not result.matched
    assert result.missing == ("unmatched",)


def test_continuation_readout_counts_typed_and_legacy_residuals() -> None:
    pkg = make_complete_package(
        continuation=ContinuationSpec(
            id="continuation",
            diagnostic_name="residual_count",
            residual_constraints=("legacy",),
            follow_up_tests=("test-1",),
            refinement_paths=("refine-1",),
            repair_paths=("repair-1",),
            residual_constraint_specs=(
                ResidualConstraintSpec(id="typed", constraint_type="follow_up"),
            ),
        )
    )

    readout = continuation_readout(pkg)

    assert readout.diagnostic_name == "residual_count"
    assert readout.residual_constraint_count == 2
    assert readout.follow_up_test_count == 1
    assert readout.has_residual_scientific_space


def test_continuation_preorder_uses_declared_residual_comparison() -> None:
    left = ResidualTransitionSystem(
        states=("l0", "l1"),
        root="l0",
        transitions=(("l0", "probe", "l1"),),
    )
    right = ResidualTransitionSystem(
        states=("r0", "r1"),
        root="r0",
        transitions=(("r0", "strong_probe", "r1"),),
    )
    comparison = ResidualComparisonSpec(
        id="probe-refinement",
        label_order=(("probe", "strong_probe"),),
        require_label_equality=False,
    )

    assert continuation_preorder(left, right, comparison=comparison)
    assert bounded_residual_simulation(left, right, comparison=comparison).matched


def test_residual_transition_system_validation_rejects_unknown_target() -> None:
    system = ResidualTransitionSystem(
        states=("s0",),
        root="s0",
        transitions=(("s0", "follow_up", "missing"),),
    )

    try:
        system.validate()
    except ValueError as exc:
        assert "unknown states" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected validation failure")


def test_continuation_preorder_result_explains_missing_labels() -> None:
    left = ResidualTransitionSystem(
        states=("l0", "l1"),
        root="l0",
        transitions=(("l0", "probe", "l1"),),
    )
    right = ResidualTransitionSystem(states=("r0",), root="r0")

    result = continuation_preorder_result(left, right)

    assert not result.matched
    assert result.missing == ("probe",)
