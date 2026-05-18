from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from cgt_availability import AvailabilityAnalyzer, AvailabilityPipeline, ClaimPackage

ROOT = Path(__file__).parents[1]
EXPERIMENT_DIR = ROOT / "experiments" / "level5_ollama_gemma4"


def load_experiment_module(name: str) -> ModuleType:
    if str(EXPERIMENT_DIR) not in sys.path:
        sys.path.insert(0, str(EXPERIMENT_DIR))
    spec = importlib.util.spec_from_file_location(name, EXPERIMENT_DIR / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_ollama_payload_disables_thinking() -> None:
    common = load_experiment_module("common")
    config = common.load_config(EXPERIMENT_DIR / "config.json")
    scenario = common.load_scenarios(EXPERIMENT_DIR / "scenario_catalog.json")[0]

    payload = common.build_ollama_payload(scenario, config, 101)

    assert payload["model"] == "gemma4:e4b"
    assert payload["think"] is False
    assert payload["stream"] is False
    assert payload["format"] == "json"
    assert payload["options"]["seed"] == 101


def test_v3_schema_guided_payload_uses_schema_and_arm_metadata() -> None:
    common = load_experiment_module("common")
    config = common.load_config(EXPERIMENT_DIR / "config_v3.json")
    scenario = common.load_scenarios(EXPERIMENT_DIR / "scenario_catalog_v2.json")[0]

    payload = common.build_ollama_payload(
        scenario,
        config,
        101,
        arm_id="schema_guided_dossier",
    )
    prompt_text = "\n".join(message["content"] for message in payload["messages"])

    assert payload["model"] == "gemma4:e4b"
    assert payload["think"] is False
    assert payload["stream"] is False
    assert isinstance(payload["format"], dict)
    assert payload["format"]["required"] == ["claim_package"]
    assert "Experiment arm: schema_guided_dossier" in prompt_text
    assert common.prompt_leakage_findings(payload, scenario) == []


def test_v4_component_slots_payload_uses_schema_mode() -> None:
    common = load_experiment_module("common")
    config = common.load_config(EXPERIMENT_DIR / "config_v4.json")
    scenario = common.load_scenarios(EXPERIMENT_DIR / "scenario_catalog_v4.json")[0]

    payload = common.build_ollama_payload(
        scenario,
        config,
        101,
        arm_id="schema_guided_component_slots",
    )
    prompt_text = "\n".join(message["content"] for message in payload["messages"])

    assert payload["model"] == "gemma4:e4b"
    assert payload["think"] is False
    assert payload["stream"] is False
    assert isinstance(payload["format"], dict)
    assert payload["format"]["required"] == ["claim_package", "component_slots"]
    assert "Experiment arm: schema_guided_component_slots" in prompt_text
    assert "`component_slots` array" in prompt_text
    assert common.prompt_leakage_findings(payload, scenario) == []


def test_v3_dry_run_covers_all_configured_arms() -> None:
    runner = load_experiment_module("run_ollama_experiment")

    result = runner.run_experiment(
        live=False,
        config_path=EXPERIMENT_DIR / "config_v3.json",
        scenario_path=EXPERIMENT_DIR / "scenario_catalog_v2.json",
        raw_output_path=EXPERIMENT_DIR / "runs" / "unit-test.raw.jsonl",
        model=None,
        think=None,
        endpoint=None,
        max_cases=1,
    )

    assert result["records_written"] == 0
    assert result["arms"] == ["minimal_text", "report_only", "schema_guided_dossier"]
    assert len(result["payload_hashes"]) == 15
    assert {item["arm_id"] for item in result["payload_hashes"]} == {
        "minimal_text",
        "report_only",
        "schema_guided_dossier",
    }


def test_v4_dry_run_covers_four_arm_matrix() -> None:
    runner = load_experiment_module("run_ollama_experiment")

    result = runner.run_experiment(
        live=False,
        config_path=EXPERIMENT_DIR / "config_v4.json",
        scenario_path=EXPERIMENT_DIR / "scenario_catalog_v4.json",
        raw_output_path=EXPERIMENT_DIR / "runs" / "unit-test-v4.raw.jsonl",
        model=None,
        think=None,
        endpoint=None,
        max_cases=1,
    )

    assert result["records_written"] == 0
    assert result["arms"] == [
        "minimal_text",
        "report_only",
        "schema_guided_dossier",
        "schema_guided_component_slots",
    ]
    assert len(result["payload_hashes"]) == 20
    assert {item["arm_id"] for item in result["payload_hashes"]} == {
        "minimal_text",
        "report_only",
        "schema_guided_dossier",
        "schema_guided_component_slots",
    }


def test_malformed_model_json_is_explicit_experiment_error() -> None:
    common = load_experiment_module("common")

    with pytest.raises(common.ExperimentError, match="not valid JSON"):
        common.response_text_to_package("{not-json")


def test_summarization_redacts_raw_response_text(tmp_path: Path) -> None:
    common = load_experiment_module("common")
    summarize = load_experiment_module("summarize_results")
    scenario = common.load_scenarios(EXPERIMENT_DIR / "scenario_catalog.json")[0]
    package = dict(scenario["gold_claim_package"])
    package["statement"] = "SECRET_RAW_ONLY_TOKEN"
    raw_record = {
        "scenario_id": scenario["id"],
        "seed": 101,
        "request_hash": "request-hash",
        "response_hash": "response-hash",
        "elapsed_ms": 12.5,
        "response": {
            "message": {
                "role": "assistant",
                "content": json.dumps({"claim_package": package}),
            }
        },
    }
    raw_path = tmp_path / "ollama_responses.raw.jsonl"
    raw_path.write_text(json.dumps(raw_record) + "\n", encoding="utf-8")
    output_dir = tmp_path / "public"

    summary = summarize.summarize_raw_outputs(
        raw_input_path=raw_path,
        output_dir=output_dir,
        scenario_path=EXPERIMENT_DIR / "scenario_catalog.json",
        config_path=EXPERIMENT_DIR / "config.json",
    )

    public_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            output_dir / "summary.json",
            output_dir / "metrics.csv",
            output_dir / "diagnostic_signatures.json",
            output_dir / "report.md",
            output_dir / "hash_manifest.json",
        )
    )
    assert summary["live_run_count"] == 1
    assert "SECRET_RAW_ONLY_TOKEN" not in public_text
    assert "response-hash" in public_text
    assert (output_dir / "diagnostic_signatures.json").exists()


def test_same_report_different_continuation_is_diagnostic_not_report_only() -> None:
    common = load_experiment_module("common")
    scenarios = {
        scenario["id"]: scenario
        for scenario in common.load_scenarios(EXPERIMENT_DIR / "scenario_catalog.json")
    }
    low = scenarios["same_report_continuation_low"]
    high = scenarios["same_report_continuation_high"]
    analyzer = AvailabilityAnalyzer(pipeline=AvailabilityPipeline.research())

    low_report = analyzer.analyze(ClaimPackage.from_dict(low["gold_claim_package"]))
    high_report = analyzer.analyze(ClaimPackage.from_dict(high["gold_claim_package"]))

    assert low["report_signature"] == high["report_signature"]
    assert low_report.status == high_report.status
    assert low_report.metadata["residual_test_count"] != high_report.metadata[
        "residual_test_count"
    ]
    assert high_report.metadata["residual_repair_count"] > low_report.metadata[
        "residual_repair_count"
    ]
    low_eval = common.evaluate_gold_package(low)
    high_eval = common.evaluate_gold_package(high)
    assert low_eval["closed_profile_signature"] == high_eval["closed_profile_signature"]
    assert (
        low_eval["cgt_diagnostic_signature_hash"]
        != high_eval["cgt_diagnostic_signature_hash"]
    )


def test_gold_theory_separation_counts_report_only_collapse() -> None:
    common = load_experiment_module("common")
    summarize = load_experiment_module("summarize_results")
    scenarios = common.load_scenarios(EXPERIMENT_DIR / "scenario_catalog.json")
    config = common.load_config(EXPERIMENT_DIR / "config.json")

    gold = summarize.evaluate_gold_scenarios(scenarios=scenarios, config=config)
    separation = gold["theory_separation"]

    assert separation["report_only_collapse_rate"] == 1.0
    assert separation["cgt_separation_rate"] == 1.0
    assert separation["continuation_sensitive_separation_count"] >= 1
    assert separation["closed_profile_separation_rate"] < separation["cgt_separation_rate"]


def test_v3_gold_theory_extends_finite_separation_cases() -> None:
    common = load_experiment_module("common")
    summarize = load_experiment_module("summarize_results")
    scenarios = common.load_scenarios(EXPERIMENT_DIR / "scenario_catalog_v2.json")
    config = common.load_config(EXPERIMENT_DIR / "config_v3.json")

    gold = summarize.evaluate_gold_scenarios(scenarios=scenarios, config=config)
    separation = gold["theory_separation"]
    evaluations = {item["scenario_id"]: item for item in gold["evaluations"]}

    assert len(scenarios) == 24
    assert separation["report_only_collapse_rate"] == 1.0
    assert separation["cgt_separation_rate"] == 1.0
    assert 0.0 < separation["closed_profile_separation_rate"] < 1.0
    omitted = evaluations["marker_state_omitted"]
    preserved = evaluations["marker_state_preserved_v3"]
    assert omitted["report_only_signature"] == preserved["report_only_signature"]
    assert omitted["closed_profile_signature"] == preserved["closed_profile_signature"]
    assert (
        omitted["cgt_diagnostic_signature_hash"]
        != preserved["cgt_diagnostic_signature_hash"]
    )
    run_result = gold["run_family_results"]["finite_run_family_almost_sure"]
    assert run_result["may_available"] is True
    assert run_result["must_available"] is False
    assert run_result["almost_sure"] is True
    assert run_result["probability_satisfying"] == 1.0


def test_v4_gold_theory_has_full_finite_dimension_separation() -> None:
    common = load_experiment_module("common")
    summarize = load_experiment_module("summarize_results")
    scenarios = common.load_scenarios(EXPERIMENT_DIR / "scenario_catalog_v4.json")
    config = common.load_config(EXPERIMENT_DIR / "config_v4.json")

    gold = summarize.evaluate_gold_scenarios(scenarios=scenarios, config=config)
    separation = gold["theory_separation"]

    assert len(scenarios) == 32
    assert separation["report_only_collapse_rate"] == 1.0
    assert separation["cgt_separation_rate"] == 1.0
    assert separation["cgt_lift_over_report_only"] == 1.0
    assert 0.0 < separation["closed_profile_separation_rate"] < 1.0
    assert separation["continuation_sensitive_separation_count"] >= 2
    assert all(
        value["accuracy"] == 1.0
        for value in separation["dimension_separation_accuracy"].values()
    )
    assert "dependency_closure" in separation["dimension_separation_accuracy"]
    assert "almost_sure" in separation["dimension_separation_accuracy"]
    assert "may_must" in separation["dimension_separation_accuracy"]

    must_result = gold["run_family_results"]["finite_run_family_must_available_v4"]
    assert must_result["may_available"] is True
    assert must_result["must_available"] is True
    assert must_result["counterexample_run_ids"] == []
    mixed_result = gold["run_family_results"]["finite_run_family_not_almost_sure_v4"]
    assert mixed_result["may_available"] is True
    assert mixed_result["must_available"] is False
    assert mixed_result["almost_sure"] is False
    assert mixed_result["probability_satisfying"] == 0.5


def test_v4_live_matrix_completeness_reports_missing_cells() -> None:
    common = load_experiment_module("common")
    summarize = load_experiment_module("summarize_results")
    scenarios = common.load_scenarios(EXPERIMENT_DIR / "scenario_catalog_v4.json")
    config = common.load_config(EXPERIMENT_DIR / "config_v4.json")
    records = [
        {
            "scenario_id": scenarios[0]["id"],
            "arm_id": "minimal_text",
            "seed": 101,
        }
    ]

    completeness = summarize.live_matrix_completeness(
        records=records,
        scenarios=scenarios,
        config=config,
    )

    assert completeness["configured_full_live_run_count"] == 640
    assert completeness["observed_live_combination_count"] == 1
    assert completeness["partial_live_run"] is True
    assert completeness["missing_live_combination_count"] == 639


def test_marker_sensitive_omission_emits_marker_and_report_only_deficiencies() -> None:
    common = load_experiment_module("common")
    scenario = next(
        item
        for item in common.load_scenarios(EXPERIMENT_DIR / "scenario_catalog.json")
        if item["id"] == "marker_sensitive_omission"
    )
    report = AvailabilityAnalyzer(pipeline=AvailabilityPipeline.research()).analyze(
        ClaimPackage.from_dict(scenario["gold_claim_package"])
    )
    codes = {item.code for item in report.dependency_closed_deficiencies}

    assert "missing_marker_policy" in codes
    assert "marker_sensitive_missing_marker_policy" in codes
    assert "report_only_insufficiency_risk" in codes


def test_marker_and_history_pairs_are_separated_by_cgt_signature() -> None:
    common = load_experiment_module("common")
    scenarios = {
        scenario["id"]: scenario
        for scenario in common.load_scenarios(EXPERIMENT_DIR / "scenario_catalog.json")
    }
    marker_missing = common.evaluate_gold_package(scenarios["marker_sensitive_omission"])
    marker_preserved = common.evaluate_gold_package(scenarios["marker_sensitive_preserved"])
    direct = common.evaluate_gold_package(scenarios["direct_selector_degeneracy"])
    structured = common.evaluate_gold_package(scenarios["structured_history_control"])

    assert marker_missing["report_only_signature"] == marker_preserved["report_only_signature"]
    assert (
        marker_missing["cgt_diagnostic_signature_hash"]
        != marker_preserved["cgt_diagnostic_signature_hash"]
    )
    assert direct["report_only_signature"] == structured["report_only_signature"]
    assert direct["cgt_diagnostic_signature_hash"] != structured[
        "cgt_diagnostic_signature_hash"
    ]


def test_run_family_gold_modes_are_may_not_must() -> None:
    common = load_experiment_module("common")
    scenario = next(
        item
        for item in common.load_scenarios(EXPERIMENT_DIR / "scenario_catalog.json")
        if item["id"] == "finite_run_family_may_must"
    )

    result = common.evaluate_run_family_spec(scenario)

    assert result is not None
    assert result["may_available"] is True
    assert result["must_available"] is False
    assert result["satisfying_run_ids"] == ["run_with_protocol"]
    assert result["counterexample_run_ids"] == ["run_missing_protocol"]


def test_gold_only_summary_needs_no_raw_file(tmp_path: Path) -> None:
    summarize = load_experiment_module("summarize_results")
    output_dir = tmp_path / "public"

    summary = summarize.summarize_gold_only(
        output_dir=output_dir,
        scenario_path=EXPERIMENT_DIR / "scenario_catalog.json",
        config_path=EXPERIMENT_DIR / "config.json",
    )

    assert summary["live_run_count"] == 0
    assert summary["gold_theory_evaluation"]["run_family_results"][
        "finite_run_family_may_must"
    ]["may_available"] is True
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "diagnostic_signatures.json").exists()


def test_v3_gold_only_writes_versioned_public_artifacts(tmp_path: Path) -> None:
    summarize = load_experiment_module("summarize_results")
    output_dir = tmp_path / "v3"

    summary = summarize.summarize_gold_only(
        output_dir=output_dir,
        scenario_path=EXPERIMENT_DIR / "scenario_catalog_v2.json",
        config_path=EXPERIMENT_DIR / "config_v3.json",
    )

    assert summary["experiment_id"] == "level5_ollama_gemma4_v3_no_think"
    assert summary["scenario_count"] == 24
    assert (output_dir / "component_coverage.csv").exists()
    assert (output_dir / "separation_matrix.csv").exists()
    public_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            output_dir / "summary.json",
            output_dir / "metrics.csv",
            output_dir / "diagnostic_signatures.json",
            output_dir / "component_coverage.csv",
            output_dir / "separation_matrix.csv",
            output_dir / "hash_manifest.json",
            output_dir / "report.md",
        )
    )
    assert "SECRET_RAW_ONLY_TOKEN" not in public_text
    assert "message.content" not in public_text
    assert "C:\\Users" not in public_text


def test_v4_gold_only_writes_theory_artifacts(tmp_path: Path) -> None:
    summarize = load_experiment_module("summarize_results")
    output_dir = tmp_path / "v4"

    summary = summarize.summarize_gold_only(
        output_dir=output_dir,
        scenario_path=EXPERIMENT_DIR / "scenario_catalog_v4.json",
        config_path=EXPERIMENT_DIR / "config_v4.json",
    )

    assert summary["experiment_id"] == "level5_ollama_gemma4_v4_finite_theory"
    assert summary["scenario_count"] == 32
    assert summary["configured_full_live_run_count"] == 640
    assert summary["cgt_lift_over_report_only"] == 1.0
    assert (output_dir / "dimension_effects.csv").exists()
    assert (output_dir / "hypothesis_tests.json").exists()
    hypothesis = json.loads((output_dir / "hypothesis_tests.json").read_text())
    assert hypothesis["primary_tests"]["all_declared_dimensions_separated"]["passed"] is True
    manifest = json.loads((output_dir / "hash_manifest.json").read_text())
    assert "dimension_effects.csv" in manifest["public_artifact_hashes"]
    assert "hypothesis_tests.json" in manifest["public_artifact_hashes"]


def test_external_backend_missing_dependency_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    external = load_experiment_module("external_analysis")
    original_import = external.importlib.import_module

    def fake_import(name: str, package: str | None = None) -> ModuleType:
        if name == "pandas":
            raise ImportError("synthetic missing pandas")
        return original_import(name, package)

    monkeypatch.setattr(external.importlib, "import_module", fake_import)

    with pytest.raises(external.ExperimentDependencyError, match="uv sync --extra experiments"):
        external.build_metrics_summary([])


def _has_external_experiment_dependencies() -> bool:
    return all(
        importlib.util.find_spec(name) is not None
        for name in ("pandas", "matplotlib", "scipy", "jsonschema")
    )


@pytest.mark.skipif(
    not _has_external_experiment_dependencies(),
    reason="experiment optional dependencies are not installed",
)
def test_external_backend_gold_only_generates_public_artifacts(tmp_path: Path) -> None:
    summarize = load_experiment_module("summarize_results")
    output_dir = tmp_path / "public"

    summary = summarize.summarize_gold_only(
        output_dir=output_dir,
        scenario_path=EXPERIMENT_DIR / "scenario_catalog.json",
        config_path=EXPERIMENT_DIR / "config.json",
        analysis_backend="external",
    )

    assert summary["analysis_backend"] == "external"
    assert "rate_confidence_intervals" in summary
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "metrics.csv").exists()
    assert (output_dir / "diagnostic_signatures.json").exists()
    assert (output_dir / "component_coverage.csv").exists()
    assert (output_dir / "separation_matrix.csv").exists()
    assert (output_dir / "metrics_summary.json").exists()
    assert (output_dir / "separation_rates.png").exists()
    manifest = json.loads((output_dir / "hash_manifest.json").read_text(encoding="utf-8"))
    assert "separation_rates.png" in manifest["public_artifact_hashes"]
    assert "component_coverage.csv" in manifest["public_artifact_hashes"]
    assert "separation_matrix.csv" in manifest["public_artifact_hashes"]


def test_baseline_negative_extraction_result_is_preserved() -> None:
    baseline = (
        EXPERIMENT_DIR
        / "results"
        / "baselines"
        / "2026-05-18-gemma4-e4b-think-false"
    )
    summary = json.loads((baseline / "summary.json").read_text(encoding="utf-8"))

    assert (baseline / "report.md").exists()
    assert summary["model"] == "gemma4:e4b"
    assert summary["think"] is False
    assert summary["live_run_count"] == 70
    assert summary["parse_error_count"] == 0
    assert summary["average_f1"] == 0.220704
    assert summary["llm_extracted_cgt_separation_rate"] == 0.0


@pytest.mark.skipif(
    not _has_external_experiment_dependencies(),
    reason="experiment optional dependencies are not installed",
)
def test_external_backend_schema_validation_rejects_bad_artifact() -> None:
    external = load_experiment_module("external_analysis")

    with pytest.raises(Exception, match="summary failed experiment JSON Schema validation"):
        external.validate_json_contracts(
            config={
                "model": "gemma4:e4b",
                "think": False,
                "stream": False,
                "format": "json",
                "pipeline": "research",
                "seed_list": [101],
            },
            scenarios=[
                {
                    "id": "case",
                    "category": "case",
                    "report_signature": "r",
                    "expected_status": "partial",
                    "expected_closed_deficiency_codes": [],
                    "gold_claim_package": {"claim_id": "case", "statement": "case"},
                }
            ],
            summary={"raw_outputs_published": True},
            metrics=[],
            diagnostic_signatures={
                "schema_version": "test",
                "raw_outputs_published": False,
                "scenario_signatures": [],
            },
        )


def test_experiment_raw_paths_are_ignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "experiments/**/raw/" in gitignore
    assert "experiments/**/runs/" in gitignore
    assert "*.raw.jsonl" in gitignore
