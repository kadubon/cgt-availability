from dataclasses import replace

from conftest import make_complete_package

from cgt_availability import (
    AvailabilityAnalyzer,
    AvailabilityPipeline,
    HistorySpec,
    PipelineLevel,
)


def test_pipeline_presets_have_stable_levels() -> None:
    presets = (
        AvailabilityPipeline.minimal(),
        AvailabilityPipeline.standard(),
        AvailabilityPipeline.interop(),
        AvailabilityPipeline.finite_theory(),
        AvailabilityPipeline.schema(),
        AvailabilityPipeline.graph(),
        AvailabilityPipeline.completion(),
        AvailabilityPipeline.research(),
    )

    assert tuple(pipeline.level for pipeline in presets) == (
        PipelineLevel.MINIMAL,
        PipelineLevel.STANDARD,
        PipelineLevel.INTEROP,
        PipelineLevel.FINITE_THEORY,
        PipelineLevel.SCHEMA,
        PipelineLevel.GRAPH,
        PipelineLevel.COMPLETION,
        PipelineLevel.RESEARCH,
    )


def test_minimal_pipeline_runs_required_components_only() -> None:
    pkg = replace(
        make_complete_package(),
        history=HistorySpec(id="history", construction_kind="direct_selector"),
        degeneracy_control=None,
    )

    report = AvailabilityAnalyzer(pipeline=AvailabilityPipeline.minimal()).analyze(pkg)

    assert report.metadata["pipeline"] == "minimal"
    assert "direct_selector_degeneracy_risk" not in {
        item.code for item in report.dependency_closed_deficiencies
    }


def test_standard_pipeline_runs_degeneracy_rule() -> None:
    pkg = replace(
        make_complete_package(),
        history=HistorySpec(id="history", construction_kind="direct_selector"),
        degeneracy_control=None,
    )

    report = AvailabilityAnalyzer(pipeline=AvailabilityPipeline.standard()).analyze(pkg)

    assert report.metadata["pipeline"] == "standard"
    assert "direct_selector_degeneracy_risk" in {
        item.code for item in report.dependency_closed_deficiencies
    }


def test_research_pipeline_declares_executable_finite_research_capabilities() -> None:
    pipeline = AvailabilityPipeline.research()

    assert pipeline.metadata["optional_extra"] == "research"
    assert "finite_dtmc_reachability" in str(
        pipeline.metadata["finite_research_capabilities"]
    )
    assert "binomial_verifier" in str(pipeline.metadata["finite_research_capabilities"])
    assert pipeline.metadata["advanced_optional_extras"] == "modelcheck,stats"
