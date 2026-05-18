"""Optional SciPy-backed statistical verifier adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, cast

from cgt_availability.adapters.base import AdapterUnavailable
from cgt_availability.core.serialization import JSONValue, ensure_json_object
from cgt_availability.core.statistics import (
    Alternative,
    BernoulliEvidence,
    StatisticalVerifierResult,
)


@dataclass(frozen=True)
class TTestEvidence:
    """Finite sample evidence for an optional one-sample t-test verifier."""

    samples: tuple[float, ...]
    null_mean: float
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def validate(self) -> None:
        if len(self.samples) < 2:
            raise ValueError("at least two samples are required for a t-test")

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


def scipy_binomial_verifier(
    evidence: BernoulliEvidence,
    *,
    null_probability: float,
    alpha: float = 0.05,
    alternative: Alternative = "greater",
    rule: str = "scipy_binomial_test",
) -> StatisticalVerifierResult:
    """Evaluate a binomial verifier through SciPy when the `stats` extra is installed."""
    stats = _scipy_stats()
    evidence.validate()
    result = stats.binomtest(
        evidence.successes,
        evidence.trials,
        p=null_probability,
        alternative=alternative,
    )
    p_value = float(result.pvalue)
    return StatisticalVerifierResult(
        verdict="pass" if p_value <= alpha else "fail",
        statistic=evidence.rate,
        p_value=p_value,
        alpha=alpha,
        alternative=alternative,
        rule=rule,
        metadata={
            "adapter": "scipy",
            "null_probability": null_probability,
            "trials": evidence.trials,
            "successes": evidence.successes,
        },
    )


def scipy_one_sample_t_test(
    evidence: TTestEvidence,
    *,
    alpha: float = 0.05,
    alternative: Alternative = "two-sided",
    rule: str = "scipy_one_sample_t_test",
) -> StatisticalVerifierResult:
    """Evaluate a one-sample t-test verifier through SciPy."""
    evidence.validate()
    if alpha <= 0.0 or alpha >= 1.0:
        raise ValueError("alpha must be between 0 and 1")
    stats = _scipy_stats()
    result = stats.ttest_1samp(
        evidence.samples,
        popmean=evidence.null_mean,
        alternative=alternative,
    )
    statistic = float(result.statistic)
    p_value = float(result.pvalue)
    return StatisticalVerifierResult(
        verdict="pass" if p_value <= alpha else "fail",
        statistic=statistic,
        p_value=p_value,
        alpha=alpha,
        alternative=alternative,
        rule=rule,
        metadata={
            "adapter": "scipy",
            "null_mean": evidence.null_mean,
            "sample_count": len(evidence.samples),
            **evidence.metadata,
        },
    )


def _scipy_stats() -> Any:
    try:
        return cast(Any, import_module("scipy.stats"))
    except ImportError as exc:
        raise AdapterUnavailable("SciPy is required; install cgt-availability[stats].") from exc
