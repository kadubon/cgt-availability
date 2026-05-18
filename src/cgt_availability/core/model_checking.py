"""Finite probabilistic model-checking helpers.

The module intentionally implements a small DTMC fragment only. It is useful for
declared finite availability models, but it is not a replacement for PRISM,
Storm, or full probabilistic temporal-logic model checking.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from cgt_availability.core.serialization import JSONValue, ensure_json_object


@dataclass(frozen=True)
class FiniteDTMC:
    """Finite discrete-time Markov chain with named states."""

    states: tuple[str, ...]
    initial: str
    transitions: dict[str, dict[str, float]]
    labels: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def validate(self, *, tolerance: float = 1e-12) -> None:
        """Validate transition support and row probabilities."""
        if self.initial not in self.states:
            raise ValueError(f"initial state is unknown: {self.initial!r}")
        state_set = set(self.states)
        missing_rows = state_set - set(self.transitions)
        if missing_rows:
            raise ValueError(f"missing transition rows: {sorted(missing_rows)}")
        for state, row in self.transitions.items():
            if state not in state_set:
                raise ValueError(f"transition row for unknown state: {state!r}")
            unknown_targets = set(row) - state_set
            if unknown_targets:
                raise ValueError(
                    f"transition row {state!r} references unknown states: "
                    f"{sorted(unknown_targets)}"
                )
            if any(probability < 0.0 for probability in row.values()):
                raise ValueError(f"transition row {state!r} has negative probability")
            total = sum(row.values())
            if abs(total - 1.0) > tolerance:
                raise ValueError(
                    f"transition row {state!r} must sum to 1.0; got {total!r}"
                )

    def target_states_for_label(self, label: str) -> tuple[str, ...]:
        """Return states carrying a declared label."""
        return tuple(
            state for state in self.states if label in set(self.labels.get(state, ()))
        )

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class ProbabilityModelCheckResult:
    """Result for a finite reachability probability query."""

    property_name: str
    probability: float
    satisfied: bool | None = None
    threshold: float | None = None
    bound: int | None = None
    target_states: tuple[str, ...] = ()
    diagnostics: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


def reachability_probability(
    chain: FiniteDTMC,
    target_states: set[str] | frozenset[str] | tuple[str, ...],
    *,
    threshold: float | None = None,
    property_name: str = "eventually_target",
    tolerance: float = 1e-12,
) -> ProbabilityModelCheckResult:
    """Compute unbounded finite DTMC reachability probability."""
    chain.validate(tolerance=tolerance)
    targets = frozenset(str(state) for state in target_states)
    _validate_targets(chain, targets)
    if chain.initial in targets:
        probability = 1.0
    else:
        can_reach_target = _states_that_can_reach(chain, targets)
        if chain.initial not in can_reach_target:
            probability = 0.0
        else:
            probability = _solve_reachability_linear_system(chain, targets, can_reach_target)
    return ProbabilityModelCheckResult(
        property_name=property_name,
        probability=probability,
        satisfied=None if threshold is None else probability >= threshold - tolerance,
        threshold=threshold,
        target_states=tuple(sorted(targets)),
        diagnostics={"method": "finite_dtmc_linear_system", "tolerance": tolerance},
    )


def bounded_reachability_probability(
    chain: FiniteDTMC,
    target_states: set[str] | frozenset[str] | tuple[str, ...],
    *,
    steps: int,
    threshold: float | None = None,
    property_name: str = "bounded_eventually_target",
    tolerance: float = 1e-12,
) -> ProbabilityModelCheckResult:
    """Compute finite DTMC reachability within at most ``steps`` transitions."""
    if steps < 0:
        raise ValueError("steps must be non-negative")
    chain.validate(tolerance=tolerance)
    targets = frozenset(str(state) for state in target_states)
    _validate_targets(chain, targets)
    probabilities = {
        state: 1.0 if state in targets else 0.0 for state in chain.states
    }
    for _ in range(steps):
        next_probabilities = dict(probabilities)
        for state in chain.states:
            if state in targets:
                next_probabilities[state] = 1.0
            else:
                next_probabilities[state] = sum(
                    probability * probabilities[target]
                    for target, probability in chain.transitions[state].items()
                )
        probabilities = next_probabilities
    probability = probabilities[chain.initial]
    return ProbabilityModelCheckResult(
        property_name=property_name,
        probability=probability,
        satisfied=None if threshold is None else probability >= threshold - tolerance,
        threshold=threshold,
        bound=steps,
        target_states=tuple(sorted(targets)),
        diagnostics={"method": "finite_dtmc_dynamic_programming", "tolerance": tolerance},
    )


def _validate_targets(chain: FiniteDTMC, targets: frozenset[str]) -> None:
    unknown = targets - set(chain.states)
    if unknown:
        raise ValueError(f"target states are unknown: {sorted(unknown)}")


def _states_that_can_reach(chain: FiniteDTMC, targets: frozenset[str]) -> frozenset[str]:
    reverse: dict[str, set[str]] = {state: set() for state in chain.states}
    for source, row in chain.transitions.items():
        for target, probability in row.items():
            if probability > 0.0:
                reverse[target].add(source)
    seen = set(targets)
    queue = deque(targets)
    while queue:
        state = queue.popleft()
        for predecessor in reverse[state]:
            if predecessor not in seen:
                seen.add(predecessor)
                queue.append(predecessor)
    return frozenset(seen)


def _solve_reachability_linear_system(
    chain: FiniteDTMC,
    targets: frozenset[str],
    can_reach_target: frozenset[str],
) -> float:
    unknowns = tuple(
        state for state in chain.states if state not in targets and state in can_reach_target
    )
    index = {state: position for position, state in enumerate(unknowns)}
    size = len(unknowns)
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    vector = [0.0 for _ in range(size)]
    for state in unknowns:
        row_index = index[state]
        matrix[row_index][row_index] = 1.0
        for target, probability in chain.transitions[state].items():
            if target in targets:
                vector[row_index] += probability
            elif target in index:
                matrix[row_index][index[target]] -= probability
    solution = _gaussian_solve(matrix, vector)
    return solution[index[chain.initial]]


def _gaussian_solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(matrix[row][column]))
        if abs(matrix[pivot][column]) < 1e-15:
            raise ValueError("linear system is singular for reachability query")
        if pivot != column:
            matrix[column], matrix[pivot] = matrix[pivot], matrix[column]
            vector[column], vector[pivot] = vector[pivot], vector[column]
        scale = matrix[column][column]
        matrix[column] = [value / scale for value in matrix[column]]
        vector[column] /= scale
        for row in range(size):
            if row == column:
                continue
            factor = matrix[row][column]
            if factor == 0.0:
                continue
            matrix[row] = [
                value - factor * matrix[column][idx] for idx, value in enumerate(matrix[row])
            ]
            vector[row] -= factor * vector[column]
    return vector
