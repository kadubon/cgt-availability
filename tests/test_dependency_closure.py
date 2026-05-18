from cgt_availability.core.deficiency import make_deficiency
from cgt_availability.core.dependencies import (
    DependencyClosure,
    DependencyCondition,
    DependencyEdge,
    DependencyGraph,
)


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


def test_induced_dependency_metadata_preserves_edge_context() -> None:
    graph = DependencyGraph(
        (
            DependencyEdge(
                source="missing_projection",
                target="missing_observation",
                source_component="projection",
                target_component="observation",
                activation_condition="projection_required",
                structured_condition=DependencyCondition.component_missing("projection"),
                rationale="Observation cannot be diagnosed before selecting a projection.",
            ),
        )
    )
    closure = DependencyClosure(graph)

    closed = closure.close_ordered((make_deficiency("missing_projection"),))
    induced = next(item for item in closed if item.code == "missing_observation")

    assert induced.depends_on == ("missing_projection",)
    assert induced.metadata["induced_by"] == "missing_projection"
    assert induced.metadata["source_component"] == "projection"
    assert induced.metadata["target_component"] == "observation"
    assert induced.metadata["activation_condition"] == "projection_required"
    assert induced.metadata["rationale"] == (
        "Observation cannot be diagnosed before selecting a projection."
    )
    assert induced.metadata["structured_condition"] == {
        "kind": "component_missing",
        "dimension": None,
        "metadata_key": None,
        "metadata_value": None,
        "component": "projection",
        "children": [],
    }


def test_dependency_closure_order_remains_deterministic_with_metadata() -> None:
    graph = DependencyGraph.from_mapping(
        {"missing_projection": ("missing_observation", "missing_description")}
    )
    closure = DependencyClosure(graph)

    first = closure.close_ordered((make_deficiency("missing_projection"),))
    second = closure.close_ordered((make_deficiency("missing_projection"),))

    assert [item.to_dict() for item in first] == [item.to_dict() for item in second]
