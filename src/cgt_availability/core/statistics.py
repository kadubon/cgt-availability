"""Finite statistical verifier helpers.

These helpers provide explicit statistical readouts for verifier plugins. They
do not decide truth; they only report finite test statistics under declared
rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from math import comb, sqrt
from typing import Any, Literal, cast

from cgt_availability.core.serialization import JSONValue, ensure_json_object

Alternative = Literal["greater", "less", "two-sided"]


@dataclass(frozen=True)
class BernoulliEvidence:
    """Finite Bernoulli evidence for a declared statistical verifier."""

    successes: int
    trials: int

    @property
    def rate(self) -> float:
        if self.trials == 0:
            raise ValueError("trials must be positive")
        return self.successes / self.trials

    def validate(self) -> None:
        if self.trials <= 0:
            raise ValueError("trials must be positive")
        if self.successes < 0 or self.successes > self.trials:
            raise ValueError("successes must satisfy 0 <= successes <= trials")

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class ConfidenceInterval:
    """Finite confidence interval readout."""

    lower: float
    upper: float
    confidence: float
    method: str

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class StatisticalVerifierResult:
    """Result of a finite statistical verifier rule."""

    verdict: str
    statistic: float
    p_value: float
    alpha: float
    alternative: Alternative
    confidence_interval: ConfidenceInterval | None = None
    rule: str = "binomial_test"
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


def binomial_p_value(
    evidence: BernoulliEvidence,
    *,
    null_probability: float,
    alternative: Alternative = "greater",
) -> float:
    """Return an exact binomial p-value, using SciPy when installed."""
    evidence.validate()
    _validate_probability(null_probability)
    scipy_value = _scipy_binomial_p_value(evidence, null_probability, alternative)
    if scipy_value is not None:
        return scipy_value
    if alternative == "greater":
        return sum(
            _binomial_pmf(k, evidence.trials, null_probability)
            for k in range(evidence.successes, evidence.trials + 1)
        )
    if alternative == "less":
        return sum(
            _binomial_pmf(k, evidence.trials, null_probability)
            for k in range(0, evidence.successes + 1)
        )
    lower = sum(
        _binomial_pmf(k, evidence.trials, null_probability)
        for k in range(0, evidence.successes + 1)
    )
    upper = sum(
        _binomial_pmf(k, evidence.trials, null_probability)
        for k in range(evidence.successes, evidence.trials + 1)
    )
    return min(1.0, 2.0 * min(lower, upper))


def wilson_score_interval(
    evidence: BernoulliEvidence,
    *,
    confidence: float = 0.95,
) -> ConfidenceInterval:
    """Return a Wilson score interval for a Bernoulli success rate."""
    evidence.validate()
    if confidence <= 0.0 or confidence >= 1.0:
        raise ValueError("confidence must be between 0 and 1")
    z = _normal_quantile(0.5 + confidence / 2.0)
    rate = evidence.rate
    denominator = 1.0 + z**2 / evidence.trials
    center = (rate + z**2 / (2.0 * evidence.trials)) / denominator
    half_width = (
        z
        * sqrt((rate * (1.0 - rate) + z**2 / (4.0 * evidence.trials)) / evidence.trials)
        / denominator
    )
    return ConfidenceInterval(
        lower=max(0.0, center - half_width),
        upper=min(1.0, center + half_width),
        confidence=confidence,
        method="wilson_score",
    )


def evaluate_binomial_verifier(
    evidence: BernoulliEvidence,
    *,
    null_probability: float,
    alpha: float = 0.05,
    alternative: Alternative = "greater",
    confidence: float = 0.95,
    rule: str = "binomial_test",
) -> StatisticalVerifierResult:
    """Evaluate a declared finite binomial verifier rule."""
    if alpha <= 0.0 or alpha >= 1.0:
        raise ValueError("alpha must be between 0 and 1")
    p_value = binomial_p_value(
        evidence,
        null_probability=null_probability,
        alternative=alternative,
    )
    interval = wilson_score_interval(evidence, confidence=confidence)
    verdict = "pass" if p_value <= alpha else "fail"
    return StatisticalVerifierResult(
        verdict=verdict,
        statistic=evidence.rate,
        p_value=p_value,
        alpha=alpha,
        alternative=alternative,
        confidence_interval=interval,
        rule=rule,
        metadata={
            "null_probability": null_probability,
            "trials": evidence.trials,
            "successes": evidence.successes,
        },
    )


def _validate_probability(value: float) -> None:
    if value < 0.0 or value > 1.0:
        raise ValueError("probability must be between 0 and 1")


def _binomial_pmf(k: int, n: int, p: float) -> float:
    return comb(n, k) * (p**k) * ((1.0 - p) ** (n - k))


def _scipy_binomial_p_value(
    evidence: BernoulliEvidence,
    null_probability: float,
    alternative: Alternative,
) -> float | None:
    try:
        stats = cast(Any, import_module("scipy.stats"))
    except ImportError:
        return None
    result = stats.binomtest(
        evidence.successes,
        evidence.trials,
        p=null_probability,
        alternative=alternative,
    )
    return float(result.pvalue)


def _normal_quantile(probability: float) -> float:
    scipy_value = _scipy_normal_quantile(probability)
    if scipy_value is not None:
        return scipy_value
    known = {
        0.95: 1.6448536269514722,
        0.975: 1.959963984540054,
        0.995: 2.5758293035489004,
    }
    rounded = round(probability, 3)
    if rounded in known:
        return known[rounded]
    raise ValueError(
        "unsupported confidence without scipy; use 0.90, 0.95, or 0.99"
    )


def _scipy_normal_quantile(probability: float) -> float | None:
    try:
        stats = cast(Any, import_module("scipy.stats"))
    except ImportError:
        return None
    return float(stats.norm.ppf(probability))
