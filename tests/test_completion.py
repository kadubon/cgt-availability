from cgt_availability import (
    RepairCandidate,
    RepairProblem,
    greedy_repair_cover,
    solve_cascaded_repair,
    solve_repair_cover,
)


def test_deficiency_repair_cover_solves_small_exact_case() -> None:
    problem = RepairProblem(
        target_deficiencies=("a", "b"),
        candidates=(
            RepairCandidate(id="a-only", name="A", repairs=("a",)),
            RepairCandidate(id="both", name="Both", repairs=("a", "b"), cost=3.0),
            RepairCandidate(id="b-only", name="B", repairs=("b",)),
        ),
    )
    plan = solve_repair_cover(problem)
    assert not plan.unrepaired
    assert {candidate.id for candidate in plan.candidates} == {"a-only", "b-only"}


def test_repair_conflicts_are_respected() -> None:
    problem = RepairProblem(
        target_deficiencies=("a", "b"),
        candidates=(
            RepairCandidate(id="a", name="A", repairs=("a",), conflicts_with=("b",)),
            RepairCandidate(id="b", name="B", repairs=("b",)),
            RepairCandidate(id="both", name="Both", repairs=("a", "b"), cost=3.0),
        ),
    )
    plan = solve_repair_cover(problem)
    assert {candidate.id for candidate in plan.candidates} == {"both"}


def test_greedy_repair_is_deterministic() -> None:
    problem = RepairProblem(
        target_deficiencies=("a", "b"),
        candidates=(
            RepairCandidate(id="b", name="B", repairs=("b",)),
            RepairCandidate(id="a", name="A", repairs=("a",)),
        ),
    )
    first = greedy_repair_cover(problem)
    second = greedy_repair_cover(problem)
    assert [candidate.id for candidate in first.candidates] == [
        candidate.id for candidate in second.candidates
    ]


def test_cascaded_repair_respects_ordered_prerequisites() -> None:
    problem = RepairProblem(
        target_deficiencies=("a", "b"),
        candidates=(
            RepairCandidate(id="repair-b", name="B", repairs=("b",), prerequisites=("a",)),
            RepairCandidate(id="repair-a", name="A", repairs=("a",)),
        ),
    )
    plan = solve_cascaded_repair(problem)
    assert not plan.unrepaired
    assert plan.applied_order == ("repair-a", "repair-b")


def test_cascaded_repair_reports_unrepaired_when_prerequisite_cannot_be_met() -> None:
    problem = RepairProblem(
        target_deficiencies=("a", "b"),
        candidates=(
            RepairCandidate(id="repair-b", name="B", repairs=("b",), prerequisites=("a",)),
        ),
    )
    plan = solve_cascaded_repair(problem)
    assert plan.unrepaired == ("a", "b")
