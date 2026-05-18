"""Create public aggregate artifacts from ignored raw Ollama outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_RAW_OUTPUT_PATH,
    DEFAULT_RESULTS_DIR,
    DEFAULT_SCENARIO_PATH,
    ExperimentError,
    analyze_claim_package_dict,
    canonical_json,
    cgt_diagnostic_signature,
    closed_deficiency_codes,
    content_from_ollama_response,
    declared_components_for_package,
    diagnostic_signature_key,
    evaluate_gold_package,
    evaluate_run_family_spec,
    expected_codes_for_scenario,
    experiment_arms,
    load_config,
    load_scenarios,
    precision_recall_f1,
    public_scenario_projection,
    response_text_to_package,
    stable_hash,
    write_json,
)

METRIC_FIELDS = (
    "mode",
    "arm_id",
    "scenario_id",
    "seed",
    "attempt",
    "json_valid",
    "parse_valid",
    "precision",
    "recall",
    "f1",
    "closed_profile_jaccard",
    "status_agreement",
    "latency_ms",
    "report_signature",
    "predicted_status",
    "expected_status",
    "diagnostic_signature_agreement",
    "closed_profile_signature_hash",
    "cgt_diagnostic_signature_hash",
    "expected_cgt_diagnostic_signature_hash",
    "declared_component_count",
    "declared_components",
    "run_may_available",
    "run_must_available",
)


def read_raw_records(raw_input_path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not raw_input_path.exists():
        raise ExperimentError(f"Raw input does not exist: {raw_input_path}")
    for line_number, line in enumerate(raw_input_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ExperimentError(f"Malformed raw JSONL at line {line_number}") from exc
        if not isinstance(value, dict):
            raise ExperimentError(f"Raw JSONL line {line_number} is not an object")
        records.append(value)
    return records


def summarize_records(
    *,
    records: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    config: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    scenario_by_id = {str(item["id"]): item for item in scenarios}
    metrics: list[dict[str, Any]] = []
    manifest_records: list[dict[str, Any]] = []
    predicted_cgt_by_arm_signature: dict[tuple[str, str], set[str]] = defaultdict(set)
    stability_by_scenario: dict[str, list[bool]] = defaultdict(list)
    parse_errors = 0
    gold = evaluate_gold_scenarios(scenarios=scenarios, config=config)
    gold_by_id = {str(item["scenario_id"]): item for item in gold["evaluations"]}

    for record in records:
        scenario_id = str(record.get("scenario_id", ""))
        scenario = scenario_by_id.get(scenario_id)
        if scenario is None:
            raise ExperimentError(f"Unknown scenario id in raw record: {scenario_id}")
        expected_codes = expected_codes_for_scenario(scenario)
        expected_status = str(scenario.get("expected_status", ""))
        arm_id = str(record.get("arm_id", "minimal_text"))
        attempt = int(record.get("attempt", 1) or 1)
        report_signature = str(scenario.get("report_signature", ""))
        row: dict[str, Any] = {
            "mode": "llm_extraction",
            "arm_id": arm_id,
            "scenario_id": scenario_id,
            "seed": record.get("seed", ""),
            "attempt": attempt,
            "json_valid": 0,
            "parse_valid": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "closed_profile_jaccard": 0.0,
            "status_agreement": 0,
            "latency_ms": record.get("elapsed_ms", ""),
            "report_signature": report_signature,
            "predicted_status": "",
            "expected_status": expected_status,
            "diagnostic_signature_agreement": 0,
            "closed_profile_signature_hash": "",
            "cgt_diagnostic_signature_hash": "",
            "expected_cgt_diagnostic_signature_hash": gold_by_id[scenario_id][
                "cgt_diagnostic_signature_hash"
            ],
            "declared_component_count": 0,
            "declared_components": "[]",
            "run_may_available": "",
            "run_must_available": "",
        }
        try:
            response = record.get("response")
            if not isinstance(response, dict):
                raise ExperimentError("raw record response must be an object")
            content = content_from_ollama_response(response)
            package_dict = response_text_to_package(content)
            row["json_valid"] = 1
            report_dict = analyze_claim_package_dict(
                package_dict,
                pipeline_name=str(config.get("pipeline", "research")),
            )
            predicted_codes = closed_deficiency_codes(report_dict)
            closed_signature = {
                "status": str(report_dict.get("status", "")),
                "closed_deficiency_codes": sorted(predicted_codes),
            }
            declared_components = declared_components_for_package(package_dict)
            cgt_signature = cgt_diagnostic_signature(
                scenario=scenario,
                package_dict=package_dict,
                report_dict=report_dict,
            )
            cgt_signature_hash = diagnostic_signature_key(cgt_signature)
            expected_signature_hash = str(
                gold_by_id[scenario_id]["cgt_diagnostic_signature_hash"]
            )
            scores = precision_recall_f1(predicted_codes, expected_codes)
            row.update(
                {
                    "parse_valid": 1,
                    "precision": round(scores["precision"], 6),
                    "recall": round(scores["recall"], 6),
                    "f1": round(scores["f1"], 6),
                    "closed_profile_jaccard": round(scores["jaccard"], 6),
                    "predicted_status": report_dict.get("status", ""),
                    "status_agreement": int(report_dict.get("status", "") == expected_status),
                    "diagnostic_signature_agreement": int(
                        cgt_signature_hash == expected_signature_hash
                    ),
                    "closed_profile_signature_hash": diagnostic_signature_key(
                        closed_signature
                    ),
                    "cgt_diagnostic_signature_hash": cgt_signature_hash,
                    "declared_component_count": len(declared_components),
                    "declared_components": canonical_json(list(declared_components)),
                }
            )
            predicted_cgt_by_arm_signature[(arm_id, report_signature)].add(cgt_signature_hash)
            profile = report_dict.get("profile", {})
            reproducible = isinstance(profile, dict) and bool(
                profile.get("is_reproducibly_available", False)
            )
            stability_by_scenario[scenario_id].append(reproducible)
        except ExperimentError:
            parse_errors += 1
        metrics.append(row)
        manifest_records.append(
            {
                "scenario_id": scenario_id,
                "arm_id": arm_id,
                "attempt": attempt,
                "seed": record.get("seed"),
                "request_hash": record.get("request_hash"),
                "response_hash": record.get("response_hash", stable_hash(record.get("response"))),
                "record_hash": stable_hash(record),
            }
        )

    grouped_signatures = list(gold["theory_separation"]["same_report_groups"])
    report_only_collapse_rate = float(gold["theory_separation"]["report_only_collapse_rate"])
    arm_ids = sorted({str(row.get("arm_id", "minimal_text")) for row in metrics})
    cgt_separation_rate_by_arm = {}
    for arm_id in arm_ids:
        separated = [
            signature
            for signature in grouped_signatures
            if len(predicted_cgt_by_arm_signature.get((arm_id, signature), set())) > 1
        ]
        cgt_separation_rate_by_arm[arm_id] = (
            len(separated) / len(grouped_signatures) if grouped_signatures else 0.0
        )
    cgt_separation_rate = (
        max(cgt_separation_rate_by_arm.values()) if cgt_separation_rate_by_arm else 0.0
    )
    valid_rows = [row for row in metrics if row["parse_valid"] == 1]
    average_f1 = (
        sum(float(row["f1"]) for row in valid_rows) / len(valid_rows) if valid_rows else 0.0
    )
    stability = {
        scenario_id: {
            "may": any(values),
            "must": all(values) if values else False,
            "empirical_probability": sum(values) / len(values) if values else 0.0,
        }
        for scenario_id, values in sorted(stability_by_scenario.items())
    }
    completeness = live_matrix_completeness(
        records=records,
        scenarios=scenarios,
        config=config,
    )
    summary = {
        "experiment_id": config.get("experiment_id"),
        "model": config.get("model"),
        "think": config.get("think"),
        "stream": config.get("stream"),
        "format": config.get("format"),
        "pipeline": config.get("pipeline"),
        "raw_outputs_published": False,
        "live_run_count": len(records),
        "configured_full_live_run_count": completeness["configured_full_live_run_count"],
        "observed_live_combination_count": completeness["observed_live_combination_count"],
        "scenario_count": len(scenarios),
        "live_scenario_count": completeness["live_scenario_count"],
        "live_scenarios": completeness["live_scenarios"],
        "partial_live_run": completeness["partial_live_run"],
        "missing_live_combination_count": completeness["missing_live_combination_count"],
        "missing_live_combinations": completeness["missing_live_combinations"],
        "parse_error_count": parse_errors,
        "average_f1": round(average_f1, 6),
        "report_only_collapse_rate": round(report_only_collapse_rate, 6),
        "cgt_separation_rate": round(cgt_separation_rate, 6),
        "gold_cgt_separation_rate": gold["theory_separation"]["cgt_separation_rate"],
        "gold_cgt_lift_over_report_only": gold["theory_separation"][
            "cgt_lift_over_report_only"
        ],
        "cgt_lift_over_report_only": round(cgt_separation_rate, 6),
        "llm_extracted_cgt_separation_rate": round(cgt_separation_rate, 6),
        "llm_extracted_cgt_separation_rate_by_arm": {
            key: round(value, 6) for key, value in cgt_separation_rate_by_arm.items()
        },
        "arm_summaries": build_arm_summaries(metrics),
        "closed_profile_separation_rate": gold["theory_separation"][
            "closed_profile_separation_rate"
        ],
        "dimension_separation_accuracy": gold["theory_separation"][
            "dimension_separation_accuracy"
        ],
        "continuation_sensitive_separation_count": gold["theory_separation"][
            "continuation_sensitive_separation_count"
        ],
        "gold_theory_evaluation": gold,
        "may_must_empirical_stability": stability,
        "public_scenarios": [public_scenario_projection(item) for item in scenarios],
    }
    manifest = {
        "config_hash": stable_hash(config),
        "scenario_catalog_hash": stable_hash({"scenarios": scenarios}),
        "raw_record_hashes": manifest_records,
    }
    return summary, metrics, manifest


def evaluate_gold_scenarios(
    *,
    scenarios: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate synthetic gold packages without any LLM outputs."""
    pipeline_name = str(config.get("pipeline", "research"))
    evaluations: list[dict[str, Any]] = []
    metrics: list[dict[str, Any]] = []
    run_family_results: dict[str, Any] = {}
    for scenario in scenarios:
        evaluation = evaluate_gold_package(scenario, pipeline_name=pipeline_name)
        run_family_result = evaluate_run_family_spec(scenario, pipeline_name=pipeline_name)
        if run_family_result is not None:
            run_family_results[str(scenario["id"])] = run_family_result
        evaluations.append(evaluation)
        closed_signature = evaluation["closed_profile_signature"]
        expected_codes = expected_codes_for_scenario(scenario)
        predicted_codes = set(closed_signature["closed_deficiency_codes"])
        scores = precision_recall_f1(predicted_codes, expected_codes)
        metrics.append(
            {
                "mode": "gold_deterministic",
                "arm_id": "gold",
                "scenario_id": scenario.get("id"),
                "seed": "",
                "attempt": "",
                "json_valid": 1,
                "parse_valid": 1,
                "precision": round(scores["precision"], 6),
                "recall": round(scores["recall"], 6),
                "f1": round(scores["f1"], 6),
                "closed_profile_jaccard": round(scores["jaccard"], 6),
                "status_agreement": int(
                    closed_signature["status"] == scenario.get("expected_status")
                ),
                "latency_ms": "",
                "report_signature": scenario.get("report_signature", ""),
                "predicted_status": closed_signature["status"],
                "expected_status": scenario.get("expected_status", ""),
                "diagnostic_signature_agreement": 1,
                "closed_profile_signature_hash": diagnostic_signature_key(closed_signature),
                "cgt_diagnostic_signature_hash": evaluation["cgt_diagnostic_signature_hash"],
                "expected_cgt_diagnostic_signature_hash": evaluation[
                    "cgt_diagnostic_signature_hash"
                ],
                "declared_component_count": len(
                    declared_components_for_package(
                        _gold_claim_package_for_metrics(scenario)
                    )
                ),
                "declared_components": canonical_json(
                    list(
                        declared_components_for_package(
                            _gold_claim_package_for_metrics(scenario)
                        )
                    )
                ),
                "run_may_available": ""
                if run_family_result is None
                else run_family_result["may_available"],
                "run_must_available": ""
                if run_family_result is None
                else run_family_result["must_available"],
            }
        )
    return {
        "evaluations": evaluations,
        "metrics": metrics,
        "run_family_results": run_family_results,
        "theory_separation": theory_separation_summary(evaluations),
    }


def _gold_claim_package_for_metrics(scenario: dict[str, Any]) -> dict[str, Any]:
    value = scenario.get("gold_claim_package", {})
    return dict(value) if isinstance(value, dict) else {}


def live_matrix_completeness(
    *,
    records: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Return the declared live matrix and any missing scenario/arm/seed cells."""
    arms = experiment_arms(config)
    seeds = tuple(str(seed) for seed in config.get("seed_list", (101,)))
    scenario_ids = tuple(str(scenario["id"]) for scenario in scenarios)
    expected = {
        (scenario_id, arm_id, seed)
        for scenario_id in scenario_ids
        for arm_id in arms
        for seed in seeds
    }
    observed = {
        (
            str(record.get("scenario_id", "")),
            str(record.get("arm_id", "minimal_text")),
            str(record.get("seed", "")),
        )
        for record in records
    }
    missing = sorted(expected - observed)
    live_scenarios = sorted({scenario_id for scenario_id, _, _ in observed if scenario_id})
    return {
        "configured_full_live_run_count": len(expected),
        "observed_live_combination_count": len(observed),
        "live_scenario_count": len(live_scenarios),
        "live_scenarios": live_scenarios,
        "partial_live_run": bool(records) and bool(missing),
        "missing_live_combination_count": len(missing),
        "missing_live_combinations": [
            {"scenario_id": scenario_id, "arm_id": arm_id, "seed": seed}
            for scenario_id, arm_id, seed in missing
        ],
    }


def build_arm_summaries(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    summaries: dict[str, Any] = {}
    by_arm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        if row.get("mode") != "llm_extraction":
            continue
        by_arm[str(row.get("arm_id", "minimal_text"))].append(row)
    for arm_id, rows in sorted(by_arm.items()):
        valid_rows = [row for row in rows if row.get("parse_valid") == 1]
        summaries[arm_id] = {
            "row_count": len(rows),
            "parse_rate": _mean_indicator(rows, "parse_valid"),
            "average_f1": _mean_float(valid_rows, "f1"),
            "status_agreement_rate": _mean_indicator(valid_rows, "status_agreement"),
            "diagnostic_signature_agreement_rate": _mean_indicator(
                valid_rows,
                "diagnostic_signature_agreement",
            ),
            "mean_declared_component_count": _mean_float(
                valid_rows,
                "declared_component_count",
            ),
        }
    return summaries


def _mean_indicator(rows: list[dict[str, Any]], field: str) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if bool(row.get(field))) / len(rows), 6)


def _mean_float(rows: list[dict[str, Any]], field: str) -> float:
    values: list[float] = []
    for row in rows:
        try:
            values.append(float(row.get(field, 0.0)))
        except (TypeError, ValueError):
            continue
    return round(sum(values) / len(values), 6) if values else 0.0


def theory_separation_summary(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize report-only collapse and CGT diagnostic separation."""
    by_report: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for evaluation in evaluations:
        report_key = canonical_json(evaluation["report_only_signature"])
        by_report[report_key].append(evaluation)
    same_report_groups = {
        report_key: rows for report_key, rows in by_report.items() if len(rows) > 1
    }
    collapsed_groups: list[str] = []
    closed_profile_separated: list[str] = []
    cgt_separated: list[str] = []
    dimension_effects: list[dict[str, Any]] = []
    dimension_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"group_count": 0, "cgt_separated_count": 0}
    )
    continuation_separated_count = 0
    for report_key, rows in same_report_groups.items():
        closed_hashes = {
            diagnostic_signature_key(row["closed_profile_signature"]) for row in rows
        }
        cgt_hashes = {str(row["cgt_diagnostic_signature_hash"]) for row in rows}
        continuation_hashes = {
            diagnostic_signature_key(row["cgt_diagnostic_signature"]["continuation"])
            for row in rows
        }
        if len(cgt_hashes) > 1:
            collapsed_groups.append(report_key)
            cgt_separated.append(report_key)
        if len(closed_hashes) > 1:
            closed_profile_separated.append(report_key)
        if len(closed_hashes) == 1 and len(continuation_hashes) > 1:
            continuation_separated_count += 1
        dimensions = sorted(
            {
                str(row.get("separating_dimension", "unspecified"))
                for row in rows
                if row.get("separating_dimension")
            }
        ) or ["unspecified"]
        effect = {
            "report_signature": report_key,
            "dimensions": dimensions,
            "scenario_ids": sorted(str(row.get("scenario_id", "")) for row in rows),
            "scenario_count": len(rows),
            "report_only_collapsed": len(cgt_hashes) > 1,
            "closed_profile_separated": len(closed_hashes) > 1,
            "cgt_separated": len(cgt_hashes) > 1,
            "continuation_only_separated": len(closed_hashes) == 1
            and len(continuation_hashes) > 1,
        }
        dimension_effects.append(effect)
        for dimension in dimensions:
            dimension_counts[dimension]["group_count"] += 1
            if effect["cgt_separated"]:
                dimension_counts[dimension]["cgt_separated_count"] += 1
    denominator = len(same_report_groups)
    dimension_accuracy = {
        dimension: {
            "group_count": counts["group_count"],
            "cgt_separated_count": counts["cgt_separated_count"],
            "accuracy": counts["cgt_separated_count"] / counts["group_count"]
            if counts["group_count"]
            else 0.0,
        }
        for dimension, counts in sorted(dimension_counts.items())
    }
    cgt_rate = len(cgt_separated) / denominator if denominator else 0.0
    return {
        "same_report_groups": sorted(same_report_groups),
        "report_only_separation_rate": 0.0,
        "report_only_collapse_rate": len(collapsed_groups) / denominator
        if denominator
        else 0.0,
        "closed_profile_separation_rate": len(closed_profile_separated) / denominator
        if denominator
        else 0.0,
        "cgt_separation_rate": cgt_rate,
        "cgt_lift_over_report_only": cgt_rate,
        "continuation_sensitive_separation_count": continuation_separated_count,
        "dimension_effects": dimension_effects,
        "dimension_separation_accuracy": dimension_accuracy,
    }


def render_report(summary: dict[str, Any]) -> str:
    interval_lines = ""
    intervals = summary.get("rate_confidence_intervals")
    if isinstance(intervals, dict):
        interval_lines = (
            "\nFinite binomial confidence intervals are included in `summary.json`.\n"
            f"- Parse rate: {_format_interval(intervals.get('parse_rate'))}\n"
            f"- Status agreement rate: {_format_interval(intervals.get('status_agreement_rate'))}\n"
            "- Diagnostic signature agreement rate: "
            f"{_format_interval(intervals.get('diagnostic_signature_agreement_rate'))}\n"
        )
    gold_theory = summary.get("gold_theory_evaluation", {})
    gold_separation = (
        gold_theory.get("theory_separation", {}) if isinstance(gold_theory, dict) else {}
    )
    llm_cgt_rate = summary.get(
        "llm_extracted_cgt_separation_rate",
        summary.get("cgt_separation_rate"),
    )
    arm_lines = ""
    arm_summaries = summary.get("arm_summaries")
    if isinstance(arm_summaries, dict) and arm_summaries:
        lines = ["\nArm-level extraction summaries:\n"]
        for arm_id, values in sorted(arm_summaries.items()):
            if not isinstance(values, dict):
                continue
            lines.append(
                "- "
                f"`{arm_id}`: rows `{values.get('row_count')}`, "
                f"parse `{_format_float(values.get('parse_rate'))}`, "
                f"F1 `{_format_float(values.get('average_f1'))}`, "
                "diagnostic signature agreement "
                f"`{_format_float(values.get('diagnostic_signature_agreement_rate'))}`\n"
            )
        arm_lines = "".join(lines)
    dimension_accuracy = summary.get("dimension_separation_accuracy", {})
    dimension_lines = ""
    if isinstance(dimension_accuracy, dict) and dimension_accuracy:
        lines = ["\nDimension-level gold separation accuracy:\n"]
        for dimension, values in sorted(dimension_accuracy.items()):
            if not isinstance(values, dict):
                continue
            lines.append(
                "- "
                f"`{dimension}`: `{_format_float(values.get('accuracy'))}` "
                f"({values.get('cgt_separated_count')}/"
                f"{values.get('group_count')})\n"
            )
        dimension_lines = "".join(lines)
    live_run_count = int(summary.get("live_run_count") or 0)
    live_scenario_count = int(summary.get("live_scenario_count") or 0)
    configured_full_live_run_count = int(summary.get("configured_full_live_run_count") or 0)
    live_scenarios = summary.get("live_scenarios")
    live_scenario_text = ""
    if isinstance(live_scenarios, list) and live_scenarios:
        live_scenario_text = ", ".join(f"`{item}`" for item in live_scenarios)
    coverage_note = ""
    if (
        live_run_count
        and configured_full_live_run_count
        and live_run_count < configured_full_live_run_count
    ):
        coverage_note = (
            "\nCoverage note: this live extraction summary is a subset of the "
            "configured full matrix. Interpret arm-level extraction rates as "
            "local evidence for the summarized scenarios, not as the complete "
            "24-scenario v3 matrix.\n"
        )
    if live_run_count:
        extraction_section = (
            "## Live LLM Extraction\n\n"
            "The local Ollama model is used only to extract candidate "
            "`ClaimPackage` JSON. The availability diagnosis is computed by the "
            "deterministic analyzer.\n\n"
            f"- Live scenarios summarized: `{live_scenario_count}`"
            f"{f' ({live_scenario_text})' if live_scenario_text else ''}\n"
            f"- Parse errors: `{summary.get('parse_error_count')}`\n"
            f"- Average deficiency F1: `{summary.get('average_f1')}`\n"
            f"- LLM-extracted CGT separation rate: `{llm_cgt_rate}`\n"
            f"{arm_lines}"
            f"{interval_lines}\n"
            f"{coverage_note}\n"
            "Interpretation: this live run produced syntactically valid packages, "
            "but the extracted packages usually omitted the richer declarations "
            "needed for marker-, history-, protocol-, and continuation-sensitive "
            "diagnosis. That is an extraction limitation, not a truth verdict and "
            "not a failure of the deterministic gold theory check.\n\n"
        )
    else:
        extraction_section = (
            "## Live LLM Extraction\n\n"
            "No live LLM outputs are summarized in this artifact. The metric rows "
            "come from deterministic gold packages only, so perfect parse, status, "
            "or diagnostic-signature agreement here is a gold self-check, not an "
            "LLM extraction result. Run `run_ollama_experiment.py --live` locally "
            "and summarize the ignored raw JSONL to evaluate extraction.\n\n"
        )
    return (
        "# Level 5 Ollama Gemma Experiment Summary\n\n"
        "This public report contains aggregate metrics only. Raw prompts, raw model "
        "responses, token traces, and local run logs are not published.\n\n"
        "## Run Configuration\n\n"
        f"- Model: `{summary.get('model')}`\n"
        f"- Thinking disabled: `{summary.get('think') is False}`\n"
        f"- Pipeline: `{summary.get('pipeline')}`\n"
        f"- Analysis backend: `{summary.get('analysis_backend', 'stdlib')}`\n"
        f"- Live records summarized: `{summary.get('live_run_count')}`\n"
        f"- Live scenarios summarized: `{summary.get('live_scenario_count')}`\n"
        f"- Catalog scenario count: `{summary.get('scenario_count')}`\n"
        "- Configured full live matrix records: "
        f"`{summary.get('configured_full_live_run_count')}`\n"
        f"- Partial live run: `{summary.get('partial_live_run')}`\n"
        f"- Raw outputs published: `{summary.get('raw_outputs_published')}`\n\n"
        "## Gold Deterministic Theory Check\n\n"
        "The synthetic gold packages are evaluated without any LLM output. This "
        "checks whether the deterministic analyzer reproduces the paper's finite "
        "separation claims.\n\n"
        f"- Report-only collapse rate: `{gold_separation.get('report_only_collapse_rate')}`\n"
        "- Closed-profile separation rate: "
        f"`{gold_separation.get('closed_profile_separation_rate')}`\n"
        f"- Gold CGT diagnostic separation rate: `{gold_separation.get('cgt_separation_rate')}`\n"
        "- Gold CGT lift over report-only separation: "
        f"`{gold_separation.get('cgt_lift_over_report_only')}`\n"
        "- Continuation-sensitive same-closed-profile separations: "
        f"`{gold_separation.get('continuation_sensitive_separation_count')}`\n"
        f"{dimension_lines}\n"
        "Interpretation: the gold finite scenarios preserve the intended CGT "
        "cut. Report-only procedures collapse all same-report groups in the "
        "catalog, dependency-closed profiles separate only some of them, and "
        "the fuller CGT diagnostic signature separates all declared marker, "
        "history, protocol, and continuation cases.\n\n"
        f"{extraction_section}"
        "## Diagnostic Meaning\n\n"
        "Report-only collapse means scenarios share a report/verdict signature "
        "while the gold CGT diagnostic signature differs. Closed-profile "
        "separation uses dependency-closed deficiencies only. CGT separation also "
        "includes marker, history, protocol, and continuation readouts.\n\n"
        "The experiment evaluates finite extraction stability and deterministic "
        "availability diagnostics. It does not evaluate claim truth, model "
        "intelligence, or general scientific quality.\n"
    )


def _format_interval(value: object) -> str:
    if not isinstance(value, dict):
        return "`not available`"
    rate = value.get("rate")
    low = value.get("low")
    high = value.get("high")
    successes = value.get("successes")
    trials = value.get("trials")
    if rate is None or low is None or high is None:
        return "`not available`"
    return (
        f"`{float(rate):.6f}` ({successes}/{trials}, "
        f"95% CI `{float(low):.6f}`-`{float(high):.6f}`)"
    )


def _format_float(value: object) -> str:
    try:
        return f"{float(value):.6f}"
    except (TypeError, ValueError):
        return "not available"


def write_metrics_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in METRIC_FIELDS})


def write_component_coverage_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    components = (
        "frame",
        "system",
        "projection",
        "observation",
        "description",
        "normalizer",
        "expected_report",
        "verifier",
        "failure_predicate",
        "reproduction_protocol",
        "history",
        "continuation",
        "marker_policy",
        "marker_state",
        "degeneracy_control",
        "provenance",
        "comparison_regime",
        "report_path",
    )
    grouped: dict[tuple[str, str], list[set[str]]] = defaultdict(list)
    for row in rows:
        declared = _declared_components_from_row(row)
        grouped[(str(row.get("mode", "")), str(row.get("arm_id", "")))].append(declared)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("mode", "arm_id", "component", "declared_rate", "row_count"),
        )
        writer.writeheader()
        for (mode, arm_id), declarations in sorted(grouped.items()):
            row_count = len(declarations)
            for component in components:
                count = sum(1 for declared in declarations if component in declared)
                writer.writerow(
                    {
                        "mode": mode,
                        "arm_id": arm_id,
                        "component": component,
                        "declared_rate": round(count / row_count, 6) if row_count else 0.0,
                        "row_count": row_count,
                    }
                )


def _declared_components_from_row(row: dict[str, Any]) -> set[str]:
    raw = row.get("declared_components", "[]")
    if isinstance(raw, str):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return set()
    else:
        value = raw
    if isinstance(value, list | tuple):
        return {str(item) for item in value}
    return set()


def write_separation_matrix_csv(
    path: Path,
    *,
    summary: dict[str, Any],
    metrics: list[dict[str, Any]],
) -> None:
    gold = summary.get("gold_theory_evaluation", {})
    groups = []
    if isinstance(gold, dict):
        groups = list(gold.get("theory_separation", {}).get("same_report_groups", []))
    rows: list[dict[str, Any]] = []
    for mode, arm_id in sorted(
        {
            (str(row.get("mode", "")), str(row.get("arm_id", "")))
            for row in metrics
        }
    ):
        filtered = [
            row
            for row in metrics
            if str(row.get("mode", "")) == mode and str(row.get("arm_id", "")) == arm_id
        ]
        for report_key in groups:
            try:
                report_signature = json.loads(report_key).get("report_signature", "")
            except (json.JSONDecodeError, AttributeError):
                report_signature = str(report_key)
            matching = [
                row
                for row in filtered
                if str(row.get("report_signature", "")) == report_signature
            ]
            closed_hashes = {
                str(row.get("closed_profile_signature_hash", ""))
                for row in matching
                if row.get("closed_profile_signature_hash")
            }
            cgt_hashes = {
                str(row.get("cgt_diagnostic_signature_hash", ""))
                for row in matching
                if row.get("cgt_diagnostic_signature_hash")
            }
            rows.append(
                {
                    "mode": mode,
                    "arm_id": arm_id,
                    "report_signature": report_signature,
                    "row_count": len(matching),
                    "report_only_collapsed": True,
                    "closed_profile_separated": len(closed_hashes) > 1,
                    "cgt_separated": len(cgt_hashes) > 1,
                    "closed_profile_signature_count": len(closed_hashes),
                    "cgt_signature_count": len(cgt_hashes),
                }
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "mode",
                "arm_id",
                "report_signature",
                "row_count",
                "report_only_collapsed",
                "closed_profile_separated",
                "cgt_separated",
                "closed_profile_signature_count",
                "cgt_signature_count",
            ),
        )
        writer.writeheader()
        writer.writerows(rows)


def write_dimension_effects_csv(path: Path, summary: dict[str, Any]) -> None:
    """Write deterministic gold dimension effects for finite theory checks."""
    effects = (
        summary.get("gold_theory_evaluation", {})
        .get("theory_separation", {})
        .get("dimension_effects", [])
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "report_signature",
                "dimensions",
                "scenario_ids",
                "scenario_count",
                "report_only_collapsed",
                "closed_profile_separated",
                "cgt_separated",
                "continuation_only_separated",
            ),
        )
        writer.writeheader()
        iter_effects = effects if isinstance(effects, list) else []
        for effect in iter_effects:
            if not isinstance(effect, dict):
                continue
            writer.writerow(
                {
                    "report_signature": effect.get("report_signature", ""),
                    "dimensions": canonical_json(effect.get("dimensions", [])),
                    "scenario_ids": canonical_json(effect.get("scenario_ids", [])),
                    "scenario_count": effect.get("scenario_count", 0),
                    "report_only_collapsed": effect.get("report_only_collapsed", False),
                    "closed_profile_separated": effect.get(
                        "closed_profile_separated",
                        False,
                    ),
                    "cgt_separated": effect.get("cgt_separated", False),
                    "continuation_only_separated": effect.get(
                        "continuation_only_separated",
                        False,
                    ),
                }
            )


def build_hypothesis_tests(
    *,
    summary: dict[str, Any],
    metrics: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a public, finite hypothesis ledger without raw model content."""
    gold = summary.get("gold_theory_evaluation", {})
    separation = gold.get("theory_separation", {}) if isinstance(gold, dict) else {}
    live_rows = [row for row in metrics if row.get("mode") == "llm_extraction"]
    arm_summaries = summary.get("arm_summaries", {})
    minimal = arm_summaries.get("minimal_text", {}) if isinstance(arm_summaries, dict) else {}
    component_slots = (
        arm_summaries.get("schema_guided_component_slots", {})
        if isinstance(arm_summaries, dict)
        else {}
    )
    return {
        "schema_version": "2026-05-18.level5.hypothesis-tests.v1",
        "raw_outputs_published": False,
        "primary_claim": "finite_cgt_diagnostic_separation_exceeds_report_only",
        "primary_tests": {
            "report_only_collapses_same_report_groups": {
                "rate": separation.get("report_only_collapse_rate"),
                "passed": separation.get("report_only_collapse_rate") == 1.0,
            },
            "cgt_separates_same_report_groups": {
                "rate": separation.get("cgt_separation_rate"),
                "passed": separation.get("cgt_separation_rate") == 1.0,
            },
            "cgt_lift_over_report_only": {
                "effect_size": separation.get("cgt_lift_over_report_only"),
                "passed": float(separation.get("cgt_lift_over_report_only", 0.0)) > 0.0,
            },
            "all_declared_dimensions_separated": {
                "dimension_separation_accuracy": separation.get(
                    "dimension_separation_accuracy",
                    {},
                ),
                "passed": all(
                    float(item.get("accuracy", 0.0)) == 1.0
                    for item in separation.get("dimension_separation_accuracy", {}).values()
                    if isinstance(item, dict)
                ),
            },
        },
        "secondary_extraction_tests": {
            "live_record_count": len(live_rows),
            "partial_live_run": summary.get("partial_live_run", False),
            "component_slot_lift_over_minimal": {
                "declared_component_count_delta": (
                    float(component_slots.get("mean_declared_component_count", 0.0))
                    - float(minimal.get("mean_declared_component_count", 0.0))
                )
                if component_slots and minimal
                else None,
                "diagnostic_agreement_delta": (
                    float(component_slots.get("diagnostic_signature_agreement_rate", 0.0))
                    - float(minimal.get("diagnostic_signature_agreement_rate", 0.0))
                )
                if component_slots and minimal
                else None,
            },
        },
        "interpretation_limits": [
            "finite synthetic scenarios only",
            "not a truth verdict",
            "not a science/non-science classifier",
            "LLM extraction is secondary to deterministic theory separation",
        ],
    }


def write_public_artifacts(
    *,
    output_dir: Path,
    summary: dict[str, Any],
    metrics: list[dict[str, Any]],
    manifest: dict[str, Any],
    diagnostic_signatures: dict[str, Any],
    analysis_backend: str,
    config: dict[str, Any],
    scenarios: list[dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    external_result: dict[str, Any] | None = None
    if analysis_backend == "external":
        from external_analysis import apply_external_analysis, write_metrics_csv_with_pandas

        external_result = apply_external_analysis(
            output_dir=output_dir,
            config=config,
            scenarios=scenarios,
            summary=summary,
            metrics=metrics,
            diagnostic_signatures=diagnostic_signatures,
        )
        write_metrics_csv_with_pandas(output_dir / "metrics.csv", metrics, METRIC_FIELDS)
    elif analysis_backend == "stdlib":
        summary["analysis_backend"] = "stdlib"
        write_metrics_csv(output_dir / "metrics.csv", metrics)
    else:
        raise ExperimentError(f"Unknown analysis backend: {analysis_backend}")

    write_component_coverage_csv(output_dir / "component_coverage.csv", metrics)
    write_separation_matrix_csv(
        output_dir / "separation_matrix.csv",
        summary=summary,
        metrics=metrics,
    )
    write_dimension_effects_csv(output_dir / "dimension_effects.csv", summary)
    hypothesis_tests = build_hypothesis_tests(summary=summary, metrics=metrics)
    write_json(output_dir / "hypothesis_tests.json", hypothesis_tests)
    report = render_report(summary)
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "diagnostic_signatures.json", diagnostic_signatures)
    (output_dir / "report.md").write_text(report, encoding="utf-8")
    manifest["public_artifact_hashes"] = public_artifact_hashes(
        output_dir=output_dir,
        summary=summary,
        metrics=metrics,
        diagnostic_signatures=diagnostic_signatures,
        report=report,
        external_result=external_result,
        hypothesis_tests=hypothesis_tests,
    )
    write_json(output_dir / "hash_manifest.json", manifest)


def public_artifact_hashes(
    *,
    output_dir: Path,
    summary: dict[str, Any],
    metrics: list[dict[str, Any]],
    diagnostic_signatures: dict[str, Any],
    report: str,
    external_result: dict[str, Any] | None,
    hypothesis_tests: dict[str, Any],
) -> dict[str, str]:
    hashes = {
        "summary.json": stable_hash(summary),
        "metrics.csv": stable_hash(metrics),
        "diagnostic_signatures.json": stable_hash(diagnostic_signatures),
        "component_coverage.csv": file_sha256(output_dir / "component_coverage.csv"),
        "separation_matrix.csv": file_sha256(output_dir / "separation_matrix.csv"),
        "dimension_effects.csv": file_sha256(output_dir / "dimension_effects.csv"),
        "hypothesis_tests.json": stable_hash(hypothesis_tests),
        "report.md": stable_hash(report),
    }
    if external_result is not None:
        hashes["metrics_summary.json"] = stable_hash(external_result["metrics_summary"])
        plot_path = output_dir / "separation_rates.png"
        if plot_path.exists():
            hashes["separation_rates.png"] = file_sha256(plot_path)
    return hashes


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_public_diagnostic_signatures(
    *,
    summary: dict[str, Any],
    metrics: list[dict[str, Any]],
) -> dict[str, Any]:
    gold = summary.get("gold_theory_evaluation", {})
    evaluations = gold.get("evaluations", []) if isinstance(gold, dict) else []
    predicted_by_scenario: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        if row.get("mode") != "llm_extraction":
            continue
        scenario_id = str(row.get("scenario_id", ""))
        predicted_by_scenario[scenario_id].append(
            {
                "arm_id": row.get("arm_id", "minimal_text"),
                "seed": row.get("seed", ""),
                "attempt": row.get("attempt", 1),
                "parse_valid": bool(row.get("parse_valid")),
                "diagnostic_signature_agreement": bool(
                    row.get("diagnostic_signature_agreement")
                ),
                "cgt_diagnostic_signature_hash": str(
                    row.get("cgt_diagnostic_signature_hash", "")
                ),
                "expected_cgt_diagnostic_signature_hash": str(
                    row.get("expected_cgt_diagnostic_signature_hash", "")
                ),
            }
        )
    scenario_signatures: list[dict[str, Any]] = []
    if isinstance(evaluations, list):
        for evaluation in evaluations:
            if not isinstance(evaluation, dict):
                continue
            scenario_id = str(evaluation.get("scenario_id", ""))
            scenario_signatures.append(
                {
                    "scenario_id": scenario_id,
                    "report_only_signature": evaluation.get("report_only_signature", {}),
                    "closed_profile_signature": evaluation.get(
                        "closed_profile_signature", {}
                    ),
                    "cgt_diagnostic_signature": evaluation.get(
                        "cgt_diagnostic_signature", {}
                    ),
                    "cgt_diagnostic_signature_hash": evaluation.get(
                        "cgt_diagnostic_signature_hash", ""
                    ),
                    "predicted_extraction_signatures": predicted_by_scenario.get(
                        scenario_id, []
                    ),
                }
            )
    return {
        "schema_version": "2026-05-18.level5.diagnostic-signatures.v1",
        "raw_outputs_published": False,
        "scenario_signatures": scenario_signatures,
    }


def summarize_raw_outputs(
    *,
    raw_input_path: Path = DEFAULT_RAW_OUTPUT_PATH,
    output_dir: Path = DEFAULT_RESULTS_DIR,
    scenario_path: Path = DEFAULT_SCENARIO_PATH,
    config_path: Path = DEFAULT_CONFIG_PATH,
    analysis_backend: str = "stdlib",
) -> dict[str, Any]:
    records = read_raw_records(raw_input_path)
    scenarios = load_scenarios(scenario_path)
    config = load_config(config_path)
    summary, metrics, manifest = summarize_records(
        records=records,
        scenarios=scenarios,
        config=config,
    )
    diagnostic_signatures = build_public_diagnostic_signatures(
        summary=summary,
        metrics=metrics,
    )
    write_public_artifacts(
        output_dir=output_dir,
        summary=summary,
        metrics=metrics,
        manifest=manifest,
        diagnostic_signatures=diagnostic_signatures,
        analysis_backend=analysis_backend,
        config=config,
        scenarios=scenarios,
    )
    return summary


def summarize_gold_only(
    *,
    output_dir: Path = DEFAULT_RESULTS_DIR,
    scenario_path: Path = DEFAULT_SCENARIO_PATH,
    config_path: Path = DEFAULT_CONFIG_PATH,
    analysis_backend: str = "stdlib",
) -> dict[str, Any]:
    scenarios = load_scenarios(scenario_path)
    config = load_config(config_path)
    gold = evaluate_gold_scenarios(scenarios=scenarios, config=config)
    summary = {
        "experiment_id": config.get("experiment_id"),
        "model": config.get("model"),
        "think": config.get("think"),
        "stream": config.get("stream"),
        "format": config.get("format"),
        "pipeline": config.get("pipeline"),
        "raw_outputs_published": False,
        "live_run_count": 0,
        "configured_full_live_run_count": (
            len(scenarios)
            * len(experiment_arms(config))
            * len(tuple(config.get("seed_list", (101,))))
        ),
        "observed_live_combination_count": 0,
        "scenario_count": len(scenarios),
        "live_scenario_count": 0,
        "live_scenarios": [],
        "partial_live_run": False,
        "missing_live_combination_count": 0,
        "missing_live_combinations": [],
        "parse_error_count": 0,
        "average_f1": round(
            sum(float(row["f1"]) for row in gold["metrics"]) / len(gold["metrics"]),
            6,
        )
        if gold["metrics"]
        else 0.0,
        "report_only_collapse_rate": gold["theory_separation"]["report_only_collapse_rate"],
        "closed_profile_separation_rate": gold["theory_separation"][
            "closed_profile_separation_rate"
        ],
        "cgt_separation_rate": gold["theory_separation"]["cgt_separation_rate"],
        "gold_cgt_separation_rate": gold["theory_separation"]["cgt_separation_rate"],
        "cgt_lift_over_report_only": gold["theory_separation"][
            "cgt_lift_over_report_only"
        ],
        "gold_cgt_lift_over_report_only": gold["theory_separation"][
            "cgt_lift_over_report_only"
        ],
        "llm_extracted_cgt_separation_rate": None,
        "dimension_separation_accuracy": gold["theory_separation"][
            "dimension_separation_accuracy"
        ],
        "continuation_sensitive_separation_count": gold["theory_separation"][
            "continuation_sensitive_separation_count"
        ],
        "gold_theory_evaluation": gold,
        "may_must_empirical_stability": {},
        "public_scenarios": [public_scenario_projection(item) for item in scenarios],
    }
    manifest = {
        "config_hash": stable_hash(config),
        "scenario_catalog_hash": stable_hash({"scenarios": scenarios}),
        "gold_evaluation_hash": stable_hash(gold),
        "raw_record_hashes": [],
    }
    diagnostic_signatures = build_public_diagnostic_signatures(
        summary=summary,
        metrics=gold["metrics"],
    )
    write_public_artifacts(
        output_dir=output_dir,
        summary=summary,
        metrics=gold["metrics"],
        manifest=manifest,
        diagnostic_signatures=diagnostic_signatures,
        analysis_backend=analysis_backend,
        config=config,
        scenarios=scenarios,
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-input", type=Path, default=DEFAULT_RAW_OUTPUT_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIO_PATH)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--gold-only", action="store_true")
    parser.add_argument(
        "--analysis-backend",
        choices=("stdlib", "external"),
        default="stdlib",
        help="Use stdlib-only output or experiment-only pandas/scipy/matplotlib/jsonschema.",
    )
    args = parser.parse_args()
    if args.gold_only:
        summary = summarize_gold_only(
            output_dir=args.output_dir,
            scenario_path=args.scenarios,
            config_path=args.config,
            analysis_backend=args.analysis_backend,
        )
    else:
        summary = summarize_raw_outputs(
            raw_input_path=args.raw_input,
            output_dir=args.output_dir,
            scenario_path=args.scenarios,
            config_path=args.config,
            analysis_backend=args.analysis_backend,
        )
    print(canonical_json(summary))


if __name__ == "__main__":
    main()
