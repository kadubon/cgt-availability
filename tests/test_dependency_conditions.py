from conftest import make_complete_package

from cgt_availability import ClaimPackage, DependencyCondition, DependencyEdge, ProjectionSpec


def test_dependency_condition_requires_dimension() -> None:
    condition = DependencyCondition.requires_dimension("continuation")

    assert condition.active_for(ClaimPackage("x", "x", metadata={"continuation_sensitive": True}))
    assert not condition.active_for(ClaimPackage("x", "x"))


def test_dependency_condition_metadata_equals_and_component_missing() -> None:
    condition = DependencyCondition.all_of(
        DependencyCondition.metadata_equals("mode", "strict"),
        DependencyCondition.component_missing("projection"),
    )

    assert condition.active_for(ClaimPackage("x", "x", metadata={"mode": "strict"}))
    assert not condition.active_for(make_complete_package(metadata={"mode": "strict"}))


def test_dependency_edge_prefers_structured_condition() -> None:
    edge = DependencyEdge(
        source="missing_continuation",
        target="report_path_type_error",
        condition="always_false",
        structured_condition=DependencyCondition.requires_dimension("continuation"),
    )

    assert edge.active_for(ClaimPackage("x", "x", metadata={"continuation_sensitive": True}))


def test_dependency_condition_component_declared_and_metadata() -> None:
    pkg = ClaimPackage(
        "x",
        "x",
        projection=ProjectionSpec(id="projection", metadata={"mode": "typed"}),
    )
    condition = DependencyCondition.all_of(
        DependencyCondition.component_present("projection"),
        DependencyCondition.component_declared("projection"),
        DependencyCondition.component_metadata_equals("projection", "mode", "typed"),
        DependencyCondition.not_(DependencyCondition.component_missing("projection")),
    )

    assert condition.active_for(pkg)
