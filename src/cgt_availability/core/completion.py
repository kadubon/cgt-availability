"""Finite deficiency repair-cover helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from itertools import combinations
from typing import Any

from cgt_availability.core.package import ClaimPackage
from cgt_availability.core.serialization import (
    JSONValue,
    ensure_json_object,
    string_dict,
    string_tuple,
)

COHERENCE_BLOCKING_CODES = (
    "report_path_type_error",
    "verifier_failure_incoherent",
    "protocol_incoherent",
    "missing_marker_policy",
    "missing_marker_provenance",
    "marker_policy_incomplete",
    "missing_continuation_diagnostic",
    "missing_continuation",
    "marker_sensitive_missing_marker_policy",
    "continuation_sensitive_missing_continuation",
)


@dataclass(frozen=True)
class RepairCandidate:
    """A candidate declaration that can repair one or more deficiencies."""

    id: str
    name: str
    repairs: tuple[str, ...]
    conflicts_with: tuple[str, ...] = ()
    prerequisites: tuple[str, ...] = ()
    cost: float = 1.0
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class PackagePatch:
    """JSON-compatible patch applied to a sandbox claim-package copy."""

    set_fields: dict[str, JSONValue] = field(default_factory=dict)
    metadata_updates: dict[str, JSONValue] = field(default_factory=dict)

    def apply(self, package: ClaimPackage) -> ClaimPackage:
        data = package.to_dict()
        for key, value in self.set_fields.items():
            data[key] = value
        metadata_value = data.get("metadata", {})
        if not isinstance(metadata_value, dict):
            raise TypeError("package metadata must be an object")
        metadata = dict(metadata_value)
        metadata.update(self.metadata_updates)
        data["metadata"] = metadata
        return ClaimPackage.from_dict(data)

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class RepairCandidatePatch:
    """Patch associated with a repair candidate id."""

    candidate_id: str
    patch: PackagePatch

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class RepairProblem:
    """A finite Deficiency Repair Cover instance."""

    target_deficiencies: tuple[str, ...]
    candidates: tuple[RepairCandidate, ...]
    max_candidates: int | None = None
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class RepairPlan:
    """A deterministic repair-cover result."""

    candidates: tuple[RepairCandidate, ...]
    repaired: tuple[str, ...]
    unrepaired: tuple[str, ...]
    total_cost: float
    conflicts: tuple[tuple[str, str], ...] = ()
    unsupported_prerequisites: tuple[str, ...] = ()
    exact: bool = True
    applied_order: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


class DeficiencyRepairCover:
    """Solver namespace for finite deficiency repair cover."""

    exact_limit = 20

    @classmethod
    def solve(cls, problem: RepairProblem) -> RepairPlan:
        if len(problem.candidates) <= cls.exact_limit:
            return solve_repair_cover(problem)
        return greedy_repair_cover(problem)

    @classmethod
    def solve_cascaded(cls, problem: RepairProblem) -> RepairPlan:
        return solve_cascaded_repair(problem)

    @classmethod
    def solve_weighted(cls, problem: RepairProblem) -> RepairPlan:
        return solve_weighted_repair_cover(problem)

    @classmethod
    def solve_coherent(cls, problem: CoherentRepairProblem) -> RepairPlan:
        return solve_coherent_repair(problem)

    @classmethod
    def solve_continuation(cls, problem: ContinuationRepairProblem) -> RepairPlan:
        return solve_continuation_repair(problem)


def solve_repair_cover(problem: RepairProblem) -> RepairPlan:
    """Solve small repair-cover problems exactly by subset enumeration."""
    candidates = tuple(sorted(problem.candidates, key=lambda item: (item.cost, item.id)))
    target = set(problem.target_deficiencies)
    best: RepairPlan | None = None
    max_size = problem.max_candidates if problem.max_candidates is not None else len(candidates)

    for size in range(max_size + 1):
        for subset in combinations(candidates, size):
            plan = _evaluate_subset(subset, target, exact=True)
            if plan.conflicts or plan.unsupported_prerequisites:
                continue
            if best is None or _plan_key(plan) < _plan_key(best):
                best = plan
    if best is not None:
        return best
    return greedy_repair_cover(problem)


def greedy_repair_cover(problem: RepairProblem) -> RepairPlan:
    """Deterministic greedy fallback for larger or unsolved instances."""
    target = set(problem.target_deficiencies)
    selected: list[RepairCandidate] = []
    repaired: set[str] = set()
    candidates = sorted(problem.candidates, key=lambda item: (item.cost, item.id))
    max_size = problem.max_candidates if problem.max_candidates is not None else len(candidates)

    while len(selected) < max_size and not target.issubset(repaired):
        available = [
            candidate
            for candidate in candidates
            if candidate not in selected
            and not _candidate_conflicts(candidate, selected)
            and set(candidate.prerequisites).issubset(repaired)
        ]
        if not available:
            break
        available.sort(
            key=lambda candidate: (
                -len(set(candidate.repairs) & (target - repaired)),
                candidate.cost,
                candidate.id,
            )
        )
        chosen = available[0]
        if not (set(chosen.repairs) & (target - repaired)):
            break
        selected.append(chosen)
        repaired.update(chosen.repairs)

    return _evaluate_subset(tuple(selected), target, exact=False)


def solve_weighted_repair_cover(
    problem: RepairProblem, *, prefer_ortools: bool = True
) -> RepairPlan:
    """Solve repair cover with an optional OR-Tools backend.

    The dependency-free exact/greedy solvers remain authoritative fallbacks. OR-Tools
    is imported only inside this function and only when requested.
    """
    if prefer_ortools:
        plan = _solve_weighted_repair_cover_ortools(problem)
        if plan is not None:
            return plan
    return DeficiencyRepairCover.solve(problem)


def solve_cascaded_repair(problem: RepairProblem) -> RepairPlan:
    """Solve ordered prerequisite-sensitive repair by explicit finite search."""
    target = set(problem.target_deficiencies)
    candidates = tuple(sorted(problem.candidates, key=lambda item: (item.cost, item.id)))
    max_size = problem.max_candidates if problem.max_candidates is not None else len(candidates)
    initially_repaired = set(string_tuple(problem.metadata.get("initially_repaired", ())))
    best = _evaluate_ordered_subset((), target, initially_repaired, exact=True)

    def search(selected: tuple[RepairCandidate, ...], repaired: set[str]) -> None:
        nonlocal best
        current = _evaluate_ordered_subset(selected, target, initially_repaired, exact=True)
        if _plan_key(current) < _plan_key(best):
            best = current
        if target.issubset(repaired) or len(selected) >= max_size:
            return
        for candidate in candidates:
            if candidate in selected:
                continue
            if _candidate_conflicts(candidate, list(selected)):
                continue
            if not set(candidate.prerequisites).issubset(repaired):
                continue
            next_repaired = repaired | set(candidate.repairs)
            search((*selected, candidate), next_repaired)

    search((), initially_repaired)
    return best


def solve_coherent_repair(problem: CoherentRepairProblem) -> RepairPlan:
    """Solve repair cover after applying candidate patches and checking coherence."""
    if problem.base_package is not None and problem.candidate_patches:
        return _solve_patch_coherent_repair(problem)

    blocked = set(problem.blocked_candidate_ids)
    filtered = RepairProblem(
        target_deficiencies=problem.repair_problem.target_deficiencies,
        candidates=tuple(
            candidate
            for candidate in problem.repair_problem.candidates
            if candidate.id not in blocked
        ),
        max_candidates=problem.repair_problem.max_candidates,
        metadata=dict(problem.repair_problem.metadata),
    )
    plan = DeficiencyRepairCover.solve(filtered)
    if plan.unrepaired:
        return plan
    return plan


def solve_continuation_repair(problem: ContinuationRepairProblem) -> RepairPlan:
    """Solve repair cover with a finite residual-effect threshold."""
    candidates = tuple(
        sorted(problem.repair_problem.candidates, key=lambda item: (item.cost, item.id))
    )
    target = set(problem.repair_problem.target_deficiencies)
    max_size = (
        problem.repair_problem.max_candidates
        if problem.repair_problem.max_candidates is not None
        else len(candidates)
    )
    best: RepairPlan | None = None
    for size in range(max_size + 1):
        for subset in combinations(candidates, size):
            if not _subset_supports_continuation_diagnostic(subset, problem):
                continue
            if _residual_effect_total(subset, problem) < problem.threshold:
                continue
            plan = _evaluate_subset(subset, target, exact=True)
            if plan.conflicts or plan.unsupported_prerequisites:
                continue
            if best is None or _plan_key(plan) < _plan_key(best):
                best = plan
    if best is not None:
        return best
    return greedy_repair_cover(problem.repair_problem)


def _solve_patch_coherent_repair(problem: CoherentRepairProblem) -> RepairPlan:
    from cgt_availability.core.analyzer import AvailabilityAnalyzer

    candidates = tuple(
        sorted(problem.repair_problem.candidates, key=lambda item: (item.cost, item.id))
    )
    target = set(problem.repair_problem.target_deficiencies)
    max_size = (
        problem.repair_problem.max_candidates
        if problem.repair_problem.max_candidates is not None
        else len(candidates)
    )
    patch_by_candidate = {
        candidate_patch.candidate_id: candidate_patch.patch
        for candidate_patch in problem.candidate_patches
    }
    analyzer = AvailabilityAnalyzer.default()
    best: RepairPlan | None = None
    for size in range(max_size + 1):
        for subset in combinations(candidates, size):
            plan = _evaluate_subset(subset, target, exact=True)
            if plan.conflicts or plan.unsupported_prerequisites or plan.unrepaired:
                continue
            patched = problem.base_package
            if patched is None:
                raise ValueError("base_package is required for patch-coherent repair")
            for candidate in subset:
                patch = patch_by_candidate.get(candidate.id)
                if patch is not None:
                    patched = patch.apply(patched)
            report = analyzer.analyze(patched)
            closed_codes = {item.code for item in report.dependency_closed_deficiencies}
            if closed_codes & set(problem.blocking_codes):
                continue
            if best is None or _plan_key(plan) < _plan_key(best):
                best = plan
    if best is not None:
        return best
    return _evaluate_subset((), target, exact=True)


def _evaluate_subset(
    subset: tuple[RepairCandidate, ...], target: set[str], *, exact: bool
) -> RepairPlan:
    repaired = set[str]()
    conflicts: list[tuple[str, str]] = []
    unsupported: list[str] = []
    selected_ids = {candidate.id for candidate in subset}

    for candidate in subset:
        repaired.update(candidate.repairs)
        for conflict_id in candidate.conflicts_with:
            if conflict_id in selected_ids:
                pair = sorted((candidate.id, conflict_id))
                conflicts.append((pair[0], pair[1]))

    for candidate in subset:
        for prerequisite in candidate.prerequisites:
            if prerequisite in target and prerequisite not in repaired:
                unsupported.append(f"{candidate.id}:{prerequisite}")

    return RepairPlan(
        candidates=tuple(sorted(subset, key=lambda item: item.id)),
        repaired=tuple(sorted(target & repaired)),
        unrepaired=tuple(sorted(target - repaired)),
        total_cost=sum(candidate.cost for candidate in subset),
        conflicts=tuple(sorted(set(conflicts))),
        unsupported_prerequisites=tuple(sorted(set(unsupported))),
        exact=exact,
    )


def _solve_weighted_repair_cover_ortools(problem: RepairProblem) -> RepairPlan | None:
    try:
        cp_model_module = import_module("ortools.sat.python.cp_model")
    except ImportError:
        return None

    cp_model = cp_model_module.CpModel()
    candidates = tuple(sorted(problem.candidates, key=lambda item: item.id))
    target = set(problem.target_deficiencies)
    variables = [cp_model.NewBoolVar(candidate.id) for candidate in candidates]

    if problem.max_candidates is not None:
        cp_model.Add(sum(variables) <= problem.max_candidates)

    for deficiency in sorted(target):
        repairers = [
            variables[index]
            for index, candidate in enumerate(candidates)
            if deficiency in candidate.repairs
        ]
        if not repairers:
            return None
        cp_model.Add(sum(repairers) >= 1)

    for index, candidate in enumerate(candidates):
        for other_index, other in enumerate(candidates[index + 1 :], start=index + 1):
            if other.id in candidate.conflicts_with or candidate.id in other.conflicts_with:
                cp_model.Add(variables[index] + variables[other_index] <= 1)

    for index, candidate in enumerate(candidates):
        for prerequisite in candidate.prerequisites:
            if prerequisite not in target:
                continue
            repairers = [
                variables[repair_index]
                for repair_index, repairer in enumerate(candidates)
                if prerequisite in repairer.repairs
            ]
            if repairers:
                cp_model.Add(variables[index] <= sum(repairers))

    scale = 1_000
    cp_model.Minimize(
        sum(
            int(candidate.cost * scale) * variables[index]
            for index, candidate in enumerate(candidates)
        )
        + sum(variables)
    )
    solver = cp_model_module.CpSolver()
    solver.parameters.enumerate_all_solutions = False
    status = solver.Solve(cp_model)
    optimal_statuses = {
        getattr(cp_model_module, "OPTIMAL", object()),
        getattr(cp_model_module, "FEASIBLE", object()),
    }
    if status not in optimal_statuses:
        return None
    selected = tuple(
        candidate
        for index, candidate in enumerate(candidates)
        if _solver_bool_value(solver, variables[index])
    )
    return _evaluate_subset(selected, target, exact=True)


def _solver_bool_value(solver: Any, variable: Any) -> bool:
    return bool(solver.BooleanValue(variable))


def _evaluate_ordered_subset(
    subset: tuple[RepairCandidate, ...],
    target: set[str],
    initially_repaired: set[str],
    *,
    exact: bool,
) -> RepairPlan:
    repaired = set(initially_repaired)
    selected: list[RepairCandidate] = []
    unsupported: list[str] = []
    for candidate in subset:
        missing = set(candidate.prerequisites) - repaired
        if missing:
            unsupported.extend(f"{candidate.id}:{item}" for item in sorted(missing))
            continue
        selected.append(candidate)
        repaired.update(candidate.repairs)
    conflicts = [
        pair
        for index, candidate in enumerate(selected)
        for pair in _conflicts_for(candidate, selected[index + 1 :])
    ]
    return RepairPlan(
        candidates=tuple(sorted(selected, key=lambda item: item.id)),
        repaired=tuple(sorted(target & repaired)),
        unrepaired=tuple(sorted(target - repaired)),
        total_cost=sum(candidate.cost for candidate in selected),
        conflicts=tuple(sorted(set(conflicts))),
        unsupported_prerequisites=tuple(sorted(set(unsupported))),
        exact=exact,
        applied_order=tuple(candidate.id for candidate in selected),
    )


def _candidate_conflicts(candidate: RepairCandidate, selected: list[RepairCandidate]) -> bool:
    selected_ids = {item.id for item in selected}
    if set(candidate.conflicts_with) & selected_ids:
        return True
    return any(candidate.id in item.conflicts_with for item in selected)


def _conflicts_for(
    candidate: RepairCandidate, selected: list[RepairCandidate]
) -> tuple[tuple[str, str], ...]:
    conflicts: list[tuple[str, str]] = []
    selected_ids = {item.id for item in selected}
    for conflict_id in candidate.conflicts_with:
        if conflict_id in selected_ids:
            pair = sorted((candidate.id, conflict_id))
            conflicts.append((pair[0], pair[1]))
    for item in selected:
        if candidate.id in item.conflicts_with:
            pair = sorted((candidate.id, item.id))
            conflicts.append((pair[0], pair[1]))
    return tuple(conflicts)


def _plan_key(plan: RepairPlan) -> tuple[int, float, int, tuple[str, ...]]:
    return (
        len(plan.unrepaired),
        plan.total_cost,
        len(plan.candidates),
        tuple(candidate.id for candidate in plan.candidates),
    )


def repair_candidate_from_dict(data: dict[str, object]) -> RepairCandidate:
    cost_value = data.get("cost", 1.0)
    if not isinstance(cost_value, str | int | float):
        raise TypeError("cost must be numeric")
    return RepairCandidate(
        id=str(data["id"]),
        name=str(data["name"]),
        repairs=string_tuple(data.get("repairs", ())),
        conflicts_with=string_tuple(data.get("conflicts_with", ())),
        prerequisites=string_tuple(data.get("prerequisites", ())),
        cost=float(cost_value),
        metadata=string_dict(data.get("metadata", {})),
    )


def repair_problem_from_dict(data: dict[str, object]) -> RepairProblem:
    candidates_value = data.get("candidates", ())
    if not isinstance(candidates_value, list | tuple):
        raise TypeError("candidates must be a sequence")
    max_candidates = data.get("max_candidates")
    if max_candidates is not None and not isinstance(max_candidates, str | int):
        raise TypeError("max_candidates must be an integer")
    return RepairProblem(
        target_deficiencies=string_tuple(data.get("target_deficiencies", ())),
        candidates=tuple(repair_candidate_from_dict(item) for item in candidates_value),
        max_candidates=None if max_candidates is None else int(max_candidates),
        metadata=string_dict(data.get("metadata", {})),
    )


@dataclass(frozen=True)
class CoherentRepairProblem:
    """Finite coherence-sensitive repair wrapper."""

    repair_problem: RepairProblem
    coherence_checks: tuple[str, ...] = ()
    blocked_candidate_ids: tuple[str, ...] = ()
    base_package: ClaimPackage | None = None
    candidate_patches: tuple[RepairCandidatePatch, ...] = ()
    blocking_codes: tuple[str, ...] = COHERENCE_BLOCKING_CODES
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class ContinuationRepairProblem:
    """Finite continuation-sensitive repair-cover instance."""

    repair_problem: RepairProblem
    residual_effects: dict[str, float] = field(default_factory=dict)
    threshold: float = 0.0
    diagnostic_name: str | None = None
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


def _residual_effect_total(
    subset: tuple[RepairCandidate, ...], problem: ContinuationRepairProblem
) -> float:
    return sum(problem.residual_effects.get(candidate.id, 0.0) for candidate in subset)


def _subset_supports_continuation_diagnostic(
    subset: tuple[RepairCandidate, ...], problem: ContinuationRepairProblem
) -> bool:
    if problem.diagnostic_name is None:
        return True
    for candidate in subset:
        raw = candidate.metadata.get("continuation_diagnostics")
        if raw is None:
            raw = candidate.metadata.get("diagnostic_name")
        diagnostics = string_tuple(raw)
        if problem.diagnostic_name in diagnostics:
            return True
    return not any(candidate.metadata for candidate in subset)
