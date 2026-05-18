import pytest

hypothesis = pytest.importorskip("hypothesis")
strategies = pytest.importorskip("hypothesis.strategies")

from cgt_availability import Deficiency, DependencyClosure  # noqa: E402


@hypothesis.given(
    strategies.lists(strategies.sampled_from(["missing_projection", "missing_observation"]))
)
def test_dependency_closure_property_idempotent(codes: list[str]) -> None:
    closure = DependencyClosure()
    deficiencies = tuple(
        Deficiency(code=code, component=code, severity="blocking", message=code)
        for code in codes
    )

    once = closure.close_ordered(deficiencies)
    twice = closure.close_ordered(once)

    assert once == twice
