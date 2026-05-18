"""Minimal continuation and residual-space helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from cgt_availability.core.package import ClaimPackage
from cgt_availability.core.serialization import JSONValue, ensure_json_object


class RunMode(StrEnum):
    """Placeholder run modes for future nondeterministic availability."""

    SINGLE = "single"
    MAY = "may"
    MUST = "must"
    ALMOST_SURE = "almost_sure"


@dataclass
class ResidualTransitionSystem:
    """Typed placeholder for future residual transition algorithms."""

    states: tuple[str, ...]
    root: str
    transitions: tuple[tuple[str, str, str], ...] = ()
    labels: dict[str, dict[str, JSONValue]] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate state membership for the finite residual transition system."""
        state_set = set(self.states)
        if self.root not in state_set:
            raise ValueError(f"root state is unknown: {self.root!r}")
        unknown_label_states = set(self.labels) - state_set
        if unknown_label_states:
            raise ValueError(f"labels reference unknown states: {sorted(unknown_label_states)}")
        for source, _label, target in self.transitions:
            unknown = {state for state in (source, target) if state not in state_set}
            if unknown:
                raise ValueError(f"transition references unknown states: {sorted(unknown)}")

    def root_labels(self) -> tuple[str, ...]:
        """Return one-step residual labels from the root state."""
        return tuple(label for source, label, _target in self.transitions if source == self.root)

    def outgoing(self, state: str) -> tuple[tuple[str, str], ...]:
        """Return outgoing (label, target) pairs for a state."""
        return tuple(
            (label, target) for source, label, target in self.transitions if source == state
        )

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class ResidualComparisonSpec:
    """Declared comparison policy for residual transition matching."""

    id: str
    label_order: tuple[tuple[str, str], ...] = ()
    require_label_equality: bool = True

    def matches(self, source_label: str, target_label: str) -> bool:
        if self.require_label_equality and source_label == target_label:
            return True
        return (source_label, target_label) in self.label_order

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class ResidualSimulationResult:
    """Finite bounded simulation result."""

    source: str
    target: str
    matched: bool
    missing: tuple[str, ...] = ()
    depth: int = 0
    bounded: bool = True

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class ContinuationReadout:
    """Diagnostic readout over a declared continuation component."""

    diagnostic_name: str | None
    residual_constraint_count: int
    follow_up_test_count: int
    refinement_path_count: int
    repair_path_count: int
    has_residual_scientific_space: bool
    required_labels: tuple[str, ...] = ()
    missing_labels: tuple[str, ...] = ()
    matched_simulation_depth: int | None = None
    utility_metric_name: str | None = None

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


def residual_test_count(pkg: ClaimPackage) -> int:
    return 0 if pkg.continuation is None else len(pkg.continuation.follow_up_tests)


def residual_refinement_count(pkg: ClaimPackage) -> int:
    return 0 if pkg.continuation is None else len(pkg.continuation.refinement_paths)


def residual_repair_count(pkg: ClaimPackage) -> int:
    return 0 if pkg.continuation is None else len(pkg.continuation.repair_paths)


def has_residual_scientific_space(pkg: ClaimPackage) -> bool:
    if pkg.continuation is None:
        return False
    continuation = pkg.continuation
    return any(
        (
            continuation.residual_constraints,
            continuation.follow_up_tests,
            continuation.refinement_paths,
            continuation.repair_paths,
            continuation.residual_constraint_specs,
        )
    )


def one_step_residual_labels(system: ResidualTransitionSystem) -> tuple[str, ...]:
    """One-step residual constraint labels from the transition-system root."""
    return tuple(sorted(system.root_labels()))


def residual_includes(left: ResidualTransitionSystem, right: ResidualTransitionSystem) -> bool:
    """Return whether left's one-step residual labels include right's labels."""
    return set(right.root_labels()).issubset(set(left.root_labels()))


def has_residual_simulation(
    source: ResidualTransitionSystem, target: ResidualTransitionSystem
) -> bool:
    """Conservative placeholder: one-step inclusion is the only supported simulation."""
    return residual_includes(target, source)


def bounded_residual_simulation(
    source: ResidualTransitionSystem,
    target: ResidualTransitionSystem,
    *,
    max_depth: int = 1,
    comparison: ResidualComparisonSpec | None = None,
) -> ResidualSimulationResult:
    """Check finite label-preserving simulation up to a bounded depth.

    The check is intentionally conservative: each outgoing label in ``source`` must
    be matched by at least one outgoing transition with the same label in ``target``.
    It does not claim full bisimulation or model checking semantics.
    """
    if max_depth < 0:
        raise ValueError("max_depth must be non-negative")
    source.validate()
    target.validate()
    missing = _missing_simulation_labels(
        source=source,
        target=target,
        state_pair=(source.root, target.root),
        max_depth=max_depth,
        comparison=comparison or ResidualComparisonSpec(id="label_equality"),
        visited=frozenset(),
    )
    return ResidualSimulationResult(
        source=source.root,
        target=target.root,
        matched=not missing,
        missing=tuple(sorted(missing)),
        depth=max_depth,
        bounded=True,
    )


def continuation_readout(pkg: ClaimPackage) -> ContinuationReadout:
    """Return finite continuation counts used by continuation-sensitive diagnostics."""
    continuation = pkg.continuation
    return ContinuationReadout(
        diagnostic_name=None if continuation is None else continuation.diagnostic_name,
        residual_constraint_count=0
        if continuation is None
        else len(continuation.residual_constraints)
        + len(continuation.residual_constraint_specs),
        follow_up_test_count=residual_test_count(pkg),
        refinement_path_count=residual_refinement_count(pkg),
        repair_path_count=residual_repair_count(pkg),
        has_residual_scientific_space=has_residual_scientific_space(pkg),
        utility_metric_name=None if continuation is None else continuation.diagnostic_name,
    )


def continuation_preorder(
    left: ResidualTransitionSystem,
    right: ResidualTransitionSystem,
    *,
    comparison: ResidualComparisonSpec | None = None,
    max_depth: int = 1,
) -> bool:
    """Return whether ``right`` has at least the residual capacity of ``left``."""
    return continuation_preorder_result(
        left,
        right,
        comparison=comparison,
        max_depth=max_depth,
    ).matched


def continuation_preorder_result(
    left: ResidualTransitionSystem,
    right: ResidualTransitionSystem,
    *,
    comparison: ResidualComparisonSpec | None = None,
    max_depth: int = 1,
) -> ResidualSimulationResult:
    """Return an explainable continuation-preorder check result."""
    return bounded_residual_simulation(
        left,
        right,
        comparison=comparison,
        max_depth=max_depth,
    )


def _missing_simulation_labels(
    *,
    source: ResidualTransitionSystem,
    target: ResidualTransitionSystem,
    state_pair: tuple[str, str],
    max_depth: int,
    comparison: ResidualComparisonSpec,
    visited: frozenset[tuple[str, str, int]],
) -> set[str]:
    source_state, target_state = state_pair
    visit_key = (source_state, target_state, max_depth)
    if visit_key in visited:
        return set()
    next_visited = visited | {visit_key}
    source_outgoing = source.outgoing(source_state)
    target_outgoing = target.outgoing(target_state)

    missing: set[str] = set()
    for label, next_source in source_outgoing:
        target_next_states = [
            next_target
            for target_label, next_target in target_outgoing
            if comparison.matches(label, target_label)
        ]
        if not target_next_states:
            missing.add(label)
            continue
        if max_depth > 0:
            nested_missing = [
                _missing_simulation_labels(
                    source=source,
                    target=target,
                    state_pair=(next_source, next_target),
                    max_depth=max_depth - 1,
                    comparison=comparison,
                    visited=next_visited,
                )
                for next_target in target_next_states
            ]
            if nested_missing and all(label_missing for label_missing in nested_missing):
                missing.update(sorted(nested_missing, key=lambda item: len(item))[0])
    return missing
