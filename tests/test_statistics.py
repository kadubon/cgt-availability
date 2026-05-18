import pytest

from cgt_availability import (
    BernoulliEvidence,
    binomial_p_value,
    evaluate_binomial_verifier,
    wilson_score_interval,
)


def test_bernoulli_evidence_rate() -> None:
    evidence = BernoulliEvidence(successes=9, trials=10)

    assert evidence.rate == 0.9
    assert evidence.to_dict() == {"successes": 9, "trials": 10}


def test_exact_binomial_p_value_without_requiring_scipy() -> None:
    evidence = BernoulliEvidence(successes=9, trials=10)

    p_value = binomial_p_value(evidence, null_probability=0.5, alternative="greater")

    assert p_value == pytest.approx(11 / 1024)


def test_wilson_interval_is_bounded_and_contains_observed_rate() -> None:
    evidence = BernoulliEvidence(successes=9, trials=10)

    interval = wilson_score_interval(evidence)

    assert 0.0 <= interval.lower <= evidence.rate <= interval.upper <= 1.0
    assert interval.method == "wilson_score"


def test_binomial_verifier_returns_declared_readout_not_truth() -> None:
    evidence = BernoulliEvidence(successes=9, trials=10)

    result = evaluate_binomial_verifier(
        evidence,
        null_probability=0.5,
        alpha=0.05,
        alternative="greater",
    )

    assert result.verdict == "pass"
    assert result.p_value == pytest.approx(11 / 1024)
    assert result.statistic == 0.9
    assert result.metadata["null_probability"] == 0.5


@pytest.mark.parametrize(
    ("successes", "trials"),
    [
        (1, 0),
        (-1, 10),
        (11, 10),
    ],
)
def test_invalid_bernoulli_evidence_fails_clearly(successes: int, trials: int) -> None:
    evidence = BernoulliEvidence(successes=successes, trials=trials)

    with pytest.raises(ValueError):
        evidence.validate()


def test_invalid_statistical_parameters_fail_clearly() -> None:
    evidence = BernoulliEvidence(successes=1, trials=2)

    with pytest.raises(ValueError, match="probability"):
        binomial_p_value(evidence, null_probability=1.5)

    with pytest.raises(ValueError, match="alpha"):
        evaluate_binomial_verifier(evidence, null_probability=0.5, alpha=1.0)

    with pytest.raises(ValueError, match="confidence"):
        wilson_score_interval(evidence, confidence=1.0)
