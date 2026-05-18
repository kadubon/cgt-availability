"""Finite nondeterministic availability helpers."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field

from cgt_availability.core.analyzer import AvailabilityAnalyzer
from cgt_availability.core.package import ClaimPackage
from cgt_availability.core.report import AvailabilityReport
from cgt_availability.core.serialization import JSONValue, ensure_json_object

AvailabilityPredicate = Callable[[AvailabilityReport], bool]


@dataclass(frozen=True)
class RunPackage:
    """A package induced by one declared finite run."""

    run_id: str
    package: ClaimPackage
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class RunAvailabilityReport:
    """May/must/almost-sure summary over a finite run family."""

    may_available: bool
    must_available: bool
    satisfying_run_ids: tuple[str, ...]
    counterexample_run_ids: tuple[str, ...]
    run_count: int
    satisfying_count: int
    probability_satisfying: float | None = None
    almost_sure: bool | None = None
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


def reproducibly_available_predicate(report: AvailabilityReport) -> bool:
    """Default package predicate for finite run-mode examples."""
    return report.profile.is_reproducibly_available


def evaluate_run_modes(
    packages: Iterable[RunPackage],
    predicate: AvailabilityPredicate = reproducibly_available_predicate,
    *,
    analyzer: AvailabilityAnalyzer | None = None,
) -> RunAvailabilityReport:
    """Evaluate finite may/must availability for declared run packages."""
    active_analyzer = analyzer or AvailabilityAnalyzer.default()
    runs = tuple(packages)
    satisfying: list[str] = []
    counterexamples: list[str] = []
    for run in runs:
        report = active_analyzer.analyze(run.package)
        if predicate(report):
            satisfying.append(run.run_id)
        else:
            counterexamples.append(run.run_id)
    return RunAvailabilityReport(
        may_available=bool(satisfying),
        must_available=bool(runs) and not counterexamples,
        satisfying_run_ids=tuple(satisfying),
        counterexample_run_ids=tuple(counterexamples),
        run_count=len(runs),
        satisfying_count=len(satisfying),
    )


def almost_sure_available(
    packages: Iterable[RunPackage],
    probabilities: Mapping[str, float],
    predicate: AvailabilityPredicate = reproducibly_available_predicate,
    *,
    analyzer: AvailabilityAnalyzer | None = None,
    tolerance: float = 1e-12,
) -> RunAvailabilityReport:
    """Evaluate finite almost-sure availability with explicit run probabilities."""
    runs = tuple(packages)
    _validate_probabilities(runs, probabilities, tolerance=tolerance)
    report = evaluate_run_modes(runs, predicate, analyzer=analyzer)
    probability_satisfying = sum(probabilities[run_id] for run_id in report.satisfying_run_ids)
    almost_sure = abs(probability_satisfying - 1.0) <= tolerance
    return RunAvailabilityReport(
        may_available=report.may_available,
        must_available=report.must_available,
        satisfying_run_ids=report.satisfying_run_ids,
        counterexample_run_ids=report.counterexample_run_ids,
        run_count=report.run_count,
        satisfying_count=report.satisfying_count,
        probability_satisfying=probability_satisfying,
        almost_sure=almost_sure,
        metadata={"tolerance": tolerance},
    )


def _validate_probabilities(
    runs: tuple[RunPackage, ...],
    probabilities: Mapping[str, float],
    *,
    tolerance: float,
) -> None:
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    run_ids = {run.run_id for run in runs}
    probability_ids = set(probabilities)
    missing = run_ids - probability_ids
    extra = probability_ids - run_ids
    if missing:
        raise ValueError(f"missing probabilities for runs: {sorted(missing)}")
    if extra:
        raise ValueError(f"probabilities provided for unknown runs: {sorted(extra)}")
    if any(value < 0.0 for value in probabilities.values()):
        raise ValueError("probabilities must be non-negative")
    total = sum(probabilities.values())
    if abs(total - 1.0) > tolerance:
        raise ValueError(f"probabilities must sum to 1.0; got {total!r}")
