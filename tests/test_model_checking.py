import pytest

from cgt_availability import (
    FiniteDTMC,
    bounded_reachability_probability,
    reachability_probability,
)


def test_finite_dtmc_reachability_probability() -> None:
    chain = FiniteDTMC(
        states=("start", "available", "blocked"),
        initial="start",
        transitions={
            "start": {"available": 0.25, "blocked": 0.75},
            "available": {"available": 1.0},
            "blocked": {"blocked": 1.0},
        },
    )

    result = reachability_probability(chain, {"available"}, threshold=0.2)

    assert result.probability == pytest.approx(0.25)
    assert result.satisfied is True
    assert result.target_states == ("available",)
    assert result.diagnostics["method"] == "finite_dtmc_linear_system"


def test_finite_dtmc_bounded_reachability_counts_transitions() -> None:
    chain = FiniteDTMC(
        states=("start", "middle", "available"),
        initial="start",
        transitions={
            "start": {"middle": 1.0},
            "middle": {"available": 1.0},
            "available": {"available": 1.0},
        },
    )

    one_step = bounded_reachability_probability(chain, {"available"}, steps=1)
    two_steps = bounded_reachability_probability(chain, {"available"}, steps=2)

    assert one_step.probability == 0.0
    assert two_steps.probability == 1.0
    assert two_steps.bound == 2


def test_finite_dtmc_label_targets() -> None:
    chain = FiniteDTMC(
        states=("start", "available"),
        initial="start",
        transitions={
            "start": {"available": 1.0},
            "available": {"available": 1.0},
        },
        labels={"available": ("reproducibly_available",)},
    )

    assert chain.target_states_for_label("reproducibly_available") == ("available",)


def test_finite_dtmc_invalid_transition_total_fails_clearly() -> None:
    chain = FiniteDTMC(
        states=("start", "available"),
        initial="start",
        transitions={
            "start": {"available": 0.9},
            "available": {"available": 1.0},
        },
    )

    with pytest.raises(ValueError, match="must sum to 1.0"):
        reachability_probability(chain, {"available"})


def test_finite_dtmc_unknown_target_fails_clearly() -> None:
    chain = FiniteDTMC(
        states=("start",),
        initial="start",
        transitions={"start": {"start": 1.0}},
    )

    with pytest.raises(ValueError, match="target states are unknown"):
        reachability_probability(chain, {"missing"})
