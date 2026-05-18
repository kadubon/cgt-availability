from cgt_availability import (
    RepairCandidate,
    RepairProblem,
    solve_repair_cover,
    solve_weighted_repair_cover,
)


def test_weighted_repair_uses_dependency_free_fallback_when_requested() -> None:
    problem = RepairProblem(
        target_deficiencies=("missing_projection", "missing_observation"),
        candidates=(
            RepairCandidate("projection", "Projection", ("missing_projection",), cost=1.0),
            RepairCandidate("observation", "Observation", ("missing_observation",), cost=1.0),
            RepairCandidate(
                "bundle",
                "Bundle",
                ("missing_projection", "missing_observation"),
                cost=3.0,
            ),
        ),
    )

    exact = solve_repair_cover(problem)
    weighted = solve_weighted_repair_cover(problem, prefer_ortools=False)

    assert weighted.repaired == exact.repaired
    assert weighted.total_cost == exact.total_cost
    assert tuple(candidate.id for candidate in weighted.candidates) == ("observation", "projection")


def test_weighted_repair_optional_backend_preserves_small_exact_result() -> None:
    problem = RepairProblem(
        target_deficiencies=("missing_verifier",),
        candidates=(RepairCandidate("verifier", "Verifier", ("missing_verifier",), cost=1.0),),
    )

    plan = solve_weighted_repair_cover(problem)

    assert plan.unrepaired == ()
    assert tuple(candidate.id for candidate in plan.candidates) == ("verifier",)
