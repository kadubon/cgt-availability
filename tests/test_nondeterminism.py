from conftest import make_complete_package

from cgt_availability import (
    ClaimPackage,
    RunPackage,
    almost_sure_available,
    evaluate_run_modes,
)


def test_may_true_must_false_for_mixed_runs() -> None:
    result = evaluate_run_modes(
        (
            RunPackage("good", make_complete_package()),
            RunPackage("bad", ClaimPackage("bad", "Undeclared run.")),
        )
    )

    assert result.may_available
    assert not result.must_available
    assert result.satisfying_run_ids == ("good",)
    assert result.counterexample_run_ids == ("bad",)


def test_must_true_when_all_runs_satisfy_predicate() -> None:
    result = evaluate_run_modes(
        (
            RunPackage("one", make_complete_package(claim_id="one")),
            RunPackage("two", make_complete_package(claim_id="two")),
        )
    )

    assert result.may_available
    assert result.must_available
    assert result.satisfying_count == 2


def test_almost_sure_true_when_bad_run_has_zero_probability() -> None:
    result = almost_sure_available(
        (
            RunPackage("good", make_complete_package()),
            RunPackage("bad", ClaimPackage("bad", "Undeclared run.")),
        ),
        {"good": 1.0, "bad": 0.0},
    )

    assert result.almost_sure is True
    assert result.probability_satisfying == 1.0
    assert not result.must_available


def test_almost_sure_rejects_missing_probabilities() -> None:
    try:
        almost_sure_available((RunPackage("run", make_complete_package()),), {})
    except ValueError as exc:
        assert "missing probabilities" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_almost_sure_rejects_probability_totals() -> None:
    try:
        almost_sure_available(
            (RunPackage("run", make_complete_package()),),
            {"run": 0.5},
        )
    except ValueError as exc:
        assert "sum to 1.0" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")
