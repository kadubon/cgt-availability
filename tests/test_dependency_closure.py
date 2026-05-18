from cgt_availability.core.deficiency import make_deficiency
from cgt_availability.core.dependencies import DependencyClosure


def test_missing_normalizer_propagates_to_verifier_and_failure_predicate() -> None:
    closure = DependencyClosure()
    closed = closure.close_ordered((make_deficiency("missing_normalizer"),))
    codes = {item.code for item in closed}
    assert "missing_verifier" in codes
    assert "missing_failure_predicate" in codes


def test_dependency_closure_close_returns_set() -> None:
    closure = DependencyClosure()
    closed = closure.close((make_deficiency("missing_projection"),))
    assert {item.code for item in closed} >= {"missing_projection", "missing_observation"}
