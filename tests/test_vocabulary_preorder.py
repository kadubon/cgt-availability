from dataclasses import replace

from conftest import make_complete_package

from cgt_availability import (
    AvailabilityAnalyzer,
    ClaimPackage,
    ContinuationSpec,
    DependencyEdge,
    DependencyGraph,
    DiagnosticVocabulary,
    availability_preorder,
)


def test_default_vocabulary_conditionally_adds_continuation_path_dependency() -> None:
    pkg = replace(make_complete_package(), metadata={"continuation_sensitive": True})
    report = AvailabilityAnalyzer.default().analyze(pkg)
    induced = [
        item
        for item in report.dependency_closed_deficiencies
        if item.code == "report_path_type_error"
    ]
    assert induced
    assert induced[0].depends_on == ("missing_continuation",)


def test_dependency_edge_carries_typed_rationale_metadata() -> None:
    edge = DependencyEdge(
        source="missing_continuation",
        target="report_path_type_error",
        source_component="continuation",
        target_component="report_path",
        activation_condition="continuation_sensitive",
        rationale="Continuation-sensitive typing requires continuation data.",
    )
    inactive = make_complete_package()
    active = replace(inactive, metadata={"continuation_sensitive": True})

    assert not edge.active_for(inactive)
    assert edge.active_for(active)
    assert edge.source_component == "continuation"
    assert edge.target_component == "report_path"
    assert edge.rationale is not None


def test_custom_vocabulary_can_add_package_relative_dependency() -> None:
    vocabulary = DiagnosticVocabulary(
        name="custom",
        dependency_graph=DependencyGraph(
            (DependencyEdge("missing_provenance", "direct_selector_degeneracy_risk"),)
        ),
    )
    pkg = ClaimPackage("x", "x")
    report = AvailabilityAnalyzer(vocabulary=vocabulary).analyze(pkg)
    assert "direct_selector_degeneracy_risk" in {
        item.code for item in report.dependency_closed_deficiencies
    }


def test_availability_preorder_compares_dependency_closed_profiles() -> None:
    bare = ClaimPackage("bare", "A bare claim.")
    complete = make_complete_package()
    assert availability_preorder(bare, complete)
    assert not availability_preorder(complete, bare)


def test_continuation_sensitive_with_diagnostic_is_profile_sensitive() -> None:
    pkg = replace(
        make_complete_package(),
        continuation=ContinuationSpec(
            id="continuation",
            residual_constraints=("probe",),
            diagnostic_name="residual_count",
        ),
        metadata={"continuation_sensitive": True},
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert report.profile.is_continuation_sensitive
