from conftest import make_complete_package

from cgt_availability import (
    CoherentRepairProblem,
    ContinuationRepairProblem,
    PackagePatch,
    RepairCandidate,
    RepairCandidatePatch,
    RepairProblem,
    solve_coherent_repair,
    solve_continuation_repair,
)


def test_coherent_repair_rejects_blocked_candidate() -> None:
    problem = CoherentRepairProblem(
        repair_problem=RepairProblem(
            target_deficiencies=("missing_verifier",),
            candidates=(
                RepairCandidate("bad", "Bad verifier", ("missing_verifier",), cost=0.1),
                RepairCandidate("good", "Good verifier", ("missing_verifier",), cost=1.0),
            ),
        ),
        coherence_checks=("verifier_failure",),
        blocked_candidate_ids=("bad",),
    )

    plan = solve_coherent_repair(problem)

    assert tuple(candidate.id for candidate in plan.candidates) == ("good",)
    assert plan.unrepaired == ()


def test_coherent_repair_evaluates_candidate_patches() -> None:
    base_package = make_complete_package(verifier=None)
    problem = CoherentRepairProblem(
        repair_problem=RepairProblem(
            target_deficiencies=("missing_verifier",),
            candidates=(
                RepairCandidate("bad", "Bad verifier", ("missing_verifier",), cost=0.1),
                RepairCandidate("good", "Good verifier", ("missing_verifier",), cost=1.0),
            ),
        ),
        base_package=base_package,
        candidate_patches=(
            RepairCandidatePatch(
                "bad",
                PackagePatch(
                    set_fields={
                        "verifier": {
                            "id": "verifier",
                            "verdict_domain": ["pass", "inconclusive"],
                        }
                    }
                ),
            ),
            RepairCandidatePatch(
                "good",
                PackagePatch(
                    set_fields={
                        "verifier": {
                            "id": "verifier",
                            "verdict_domain": ["pass", "fail", "inconclusive"],
                        }
                    }
                ),
            ),
        ),
    )

    plan = solve_coherent_repair(problem)

    assert tuple(candidate.id for candidate in plan.candidates) == ("good",)
    assert plan.unrepaired == ()


def test_continuation_repair_respects_residual_threshold() -> None:
    problem = ContinuationRepairProblem(
        repair_problem=RepairProblem(
            target_deficiencies=("missing_continuation",),
            candidates=(
                RepairCandidate("small", "Small continuation", ("missing_continuation",), cost=0.1),
                RepairCandidate("large", "Large continuation", ("missing_continuation",), cost=2.0),
            ),
        ),
        residual_effects={"small": 0.1, "large": 2.0},
        threshold=1.0,
        diagnostic_name="residual_count",
    )

    plan = solve_continuation_repair(problem)

    assert tuple(candidate.id for candidate in plan.candidates) == ("large",)
    assert plan.unrepaired == ()


def test_continuation_repair_uses_declared_diagnostic_name() -> None:
    problem = ContinuationRepairProblem(
        repair_problem=RepairProblem(
            target_deficiencies=("missing_continuation",),
            candidates=(
                RepairCandidate(
                    "wrong",
                    "Wrong diagnostic",
                    ("missing_continuation",),
                    metadata={"continuation_diagnostics": ["other"]},
                ),
                RepairCandidate(
                    "right",
                    "Right diagnostic",
                    ("missing_continuation",),
                    cost=2.0,
                    metadata={"continuation_diagnostics": ["residual_count"]},
                ),
            ),
        ),
        residual_effects={"wrong": 10.0, "right": 1.0},
        threshold=1.0,
        diagnostic_name="residual_count",
    )

    plan = solve_continuation_repair(problem)

    assert tuple(candidate.id for candidate in plan.candidates) == ("right",)
