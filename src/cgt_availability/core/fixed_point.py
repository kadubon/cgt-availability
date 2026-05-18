"""Finite fixed-point helpers for dependency operators."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from cgt_availability.core.serialization import JSONValue, ensure_json_object

DeficiencyOperator = Callable[[frozenset[str]], Iterable[str]]


@dataclass(frozen=True)
class FixedPointResult:
    """Finite least fixed-point iteration result."""

    initial: tuple[str, ...]
    fixed_point: tuple[str, ...]
    iterations: tuple[tuple[str, ...], ...]
    added_by_step: tuple[tuple[str, ...], ...]
    stabilization_step: int | None
    converged: bool
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


def least_fixed_point(
    initial: Iterable[str],
    operator: DeficiencyOperator,
    *,
    max_steps: int | None = None,
) -> FixedPointResult:
    """Compute a finite Kleene-style least fixed point over deficiency codes.

    This is an executable finite approximation of the infinitary dependency
    operator in the paper. It does not implement transfinite ordinal iteration.
    """
    if max_steps is not None and max_steps < 0:
        raise ValueError("max_steps must be non-negative")

    current = frozenset(str(item) for item in initial)
    iterations: list[tuple[str, ...]] = [tuple(sorted(current))]
    added_by_step: list[tuple[str, ...]] = []
    step = 0

    while max_steps is None or step < max_steps:
        produced = frozenset(str(item) for item in operator(current))
        next_profile = current | produced
        added = tuple(sorted(next_profile - current))
        added_by_step.append(added)
        step += 1
        if next_profile == current:
            return FixedPointResult(
                initial=iterations[0],
                fixed_point=tuple(sorted(current)),
                iterations=tuple(iterations),
                added_by_step=tuple(added_by_step),
                stabilization_step=step - 1,
                converged=True,
            )
        current = next_profile
        iterations.append(tuple(sorted(current)))

    return FixedPointResult(
        initial=iterations[0],
        fixed_point=tuple(sorted(current)),
        iterations=tuple(iterations),
        added_by_step=tuple(added_by_step),
        stabilization_step=None,
        converged=False,
        metadata={"max_steps": max_steps},
    )
