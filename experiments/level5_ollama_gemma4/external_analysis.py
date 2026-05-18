"""Optional external-library analysis backend for the Level 5 experiment."""

from __future__ import annotations

import importlib
import math
from pathlib import Path
from typing import Any

from common import ExperimentError, stable_hash, write_json

CONFIG_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["model", "think", "stream", "format", "pipeline", "seed_list"],
    "properties": {
        "model": {"type": "string"},
        "think": {"type": "boolean"},
        "stream": {"type": "boolean"},
        "format": {"type": "string"},
        "pipeline": {"type": "string"},
        "seed_list": {"type": "array", "items": {"type": "integer"}},
    },
    "additionalProperties": True,
}

SCENARIO_CATALOG_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["scenarios"],
    "properties": {
        "scenarios": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "id",
                    "category",
                    "report_signature",
                    "expected_status",
                    "expected_closed_deficiency_codes",
                    "gold_claim_package",
                ],
                "properties": {
                    "id": {"type": "string"},
                    "category": {"type": "string"},
                    "report_signature": {"type": "string"},
                    "expected_status": {"type": "string"},
                    "expected_closed_deficiency_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "gold_claim_package": {
                        "type": "object",
                        "required": ["claim_id", "statement"],
                    },
                },
                "additionalProperties": True,
            },
        }
    },
    "additionalProperties": True,
}

SUMMARY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "experiment_id",
        "model",
        "think",
        "pipeline",
        "raw_outputs_published",
        "scenario_count",
        "report_only_collapse_rate",
        "cgt_separation_rate",
        "analysis_backend",
    ],
    "properties": {
        "raw_outputs_published": {"const": False},
        "scenario_count": {"type": "integer", "minimum": 0},
        "report_only_collapse_rate": {"type": "number"},
        "closed_profile_separation_rate": {"type": "number"},
        "cgt_separation_rate": {"type": "number"},
        "analysis_backend": {"enum": ["stdlib", "external"]},
    },
    "additionalProperties": True,
}

METRICS_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["mode", "scenario_id", "parse_valid", "f1"],
        "properties": {
            "mode": {"type": "string"},
            "scenario_id": {"type": "string"},
            "parse_valid": {"type": ["integer", "boolean"]},
            "f1": {"type": "number"},
        },
        "additionalProperties": True,
    },
}

DIAGNOSTIC_SIGNATURES_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["schema_version", "raw_outputs_published", "scenario_signatures"],
    "properties": {
        "schema_version": {"type": "string"},
        "raw_outputs_published": {"const": False},
        "scenario_signatures": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "scenario_id",
                    "report_only_signature",
                    "closed_profile_signature",
                    "cgt_diagnostic_signature_hash",
                ],
                "additionalProperties": True,
            },
        },
    },
    "additionalProperties": True,
}


class ExperimentDependencyError(ExperimentError):
    """Raised when the optional experiment backend is requested without extras."""


def import_external_package(name: str) -> Any:
    """Import an experiment-only dependency with an explicit installation hint."""
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise ExperimentDependencyError(
            f"External analysis backend requires `{name}`. "
            "Install experiment dependencies with `uv sync --extra experiments`."
        ) from exc


def validate_json_contracts(
    *,
    config: dict[str, Any],
    scenarios: list[dict[str, Any]],
    summary: dict[str, Any],
    metrics: list[dict[str, Any]],
    diagnostic_signatures: dict[str, Any],
) -> None:
    """Validate public experiment contracts with jsonschema."""
    jsonschema = import_external_package("jsonschema")
    checks = (
        ("config", config, CONFIG_SCHEMA),
        ("scenario_catalog", {"scenarios": scenarios}, SCENARIO_CATALOG_SCHEMA),
        ("summary", summary, SUMMARY_SCHEMA),
        ("metrics", metrics, METRICS_SCHEMA),
        ("diagnostic_signatures", diagnostic_signatures, DIAGNOSTIC_SIGNATURES_SCHEMA),
    )
    for name, instance, schema in checks:
        try:
            jsonschema.validate(instance=instance, schema=schema)
        except jsonschema.exceptions.ValidationError as exc:
            raise ExperimentError(f"{name} failed experiment JSON Schema validation") from exc


def build_metrics_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build grouped metric tables with pandas for public aggregate reporting."""
    pandas = import_external_package("pandas")
    frame = pandas.DataFrame(rows)
    if frame.empty:
        return {"row_count": 0, "by_mode": []}

    numeric_columns = (
        "parse_valid",
        "json_valid",
        "precision",
        "recall",
        "f1",
        "closed_profile_jaccard",
        "status_agreement",
        "diagnostic_signature_agreement",
        "declared_component_count",
        "latency_ms",
    )
    for column in numeric_columns:
        if column in frame.columns:
            frame[column] = pandas.to_numeric(frame[column], errors="coerce")

    grouped = (
        frame.groupby("mode", dropna=False)
        .agg(
            row_count=("scenario_id", "count"),
            parse_rate=("parse_valid", "mean"),
            json_rate=("json_valid", "mean"),
            mean_f1=("f1", "mean"),
            mean_closed_profile_jaccard=("closed_profile_jaccard", "mean"),
            status_agreement_rate=("status_agreement", "mean"),
            diagnostic_signature_agreement_rate=(
                "diagnostic_signature_agreement",
                "mean",
            ),
            mean_latency_ms=("latency_ms", "mean"),
        )
        .reset_index()
    )
    result = {
        "row_count": int(len(frame)),
        "by_mode": _json_clean(grouped.to_dict(orient="records")),
    }
    if "arm_id" in frame.columns:
        by_arm = (
            frame.groupby(["mode", "arm_id"], dropna=False)
            .agg(
                row_count=("scenario_id", "count"),
                parse_rate=("parse_valid", "mean"),
                mean_f1=("f1", "mean"),
                diagnostic_signature_agreement_rate=(
                    "diagnostic_signature_agreement",
                    "mean",
                ),
                mean_declared_component_count=("declared_component_count", "mean")
                if "declared_component_count" in frame.columns
                else ("scenario_id", "count"),
            )
            .reset_index()
        )
        result["by_arm"] = _json_clean(by_arm.to_dict(orient="records"))
    return result


def build_rate_intervals(
    *,
    summary: dict[str, Any],
    metrics: list[dict[str, Any]],
    confidence_level: float = 0.95,
) -> dict[str, Any]:
    """Compute finite binomial confidence intervals with SciPy."""
    stats = import_external_package("scipy.stats")
    live_rows = [row for row in metrics if row.get("mode") == "llm_extraction"]
    measured_rows = live_rows or metrics
    intervals = {
        "parse_rate": _interval_from_rows(
            stats,
            rows=measured_rows,
            field="parse_valid",
            confidence_level=confidence_level,
        ),
        "status_agreement_rate": _interval_from_rows(
            stats,
            rows=measured_rows,
            field="status_agreement",
            confidence_level=confidence_level,
        ),
        "diagnostic_signature_agreement_rate": _interval_from_rows(
            stats,
            rows=measured_rows,
            field="diagnostic_signature_agreement",
            confidence_level=confidence_level,
        ),
    }
    separation = (
        summary.get("gold_theory_evaluation", {})
        .get("theory_separation", {})
        .get("same_report_groups", [])
    )
    group_count = len(separation) if isinstance(separation, list) else 0
    for field in (
        "report_only_collapse_rate",
        "closed_profile_separation_rate",
        "cgt_separation_rate",
    ):
        rate = float(summary.get(field, 0.0))
        intervals[field] = _binomial_interval(
            stats,
            successes=int(round(rate * group_count)),
            trials=group_count,
            confidence_level=confidence_level,
        )
    return intervals


def write_metrics_csv_with_pandas(
    path: Path,
    rows: list[dict[str, Any]],
    fields: tuple[str, ...],
) -> None:
    """Write metrics with pandas while preserving the public column order."""
    pandas = import_external_package("pandas")
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pandas.DataFrame(rows)
    for field in fields:
        if field not in frame.columns:
            frame[field] = ""
    frame.loc[:, list(fields)].to_csv(path, index=False)


def write_separation_plot(path: Path, summary: dict[str, Any]) -> None:
    """Write a public aggregate plot without raw prompt or response content."""
    matplotlib = import_external_package("matplotlib")
    matplotlib.use("Agg")
    pyplot = import_external_package("matplotlib.pyplot")
    labels = ["Report-only collapse", "Closed-profile", "CGT"]
    values = [
        float(summary.get("report_only_collapse_rate", 0.0)),
        float(summary.get("closed_profile_separation_rate", 0.0)),
        float(summary.get("gold_cgt_separation_rate", summary.get("cgt_separation_rate", 0.0))),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = pyplot.subplots(figsize=(7.2, 4.2))
    bars = axes.bar(labels, values, color=["#6b7280", "#2563eb", "#0f766e"])
    axes.set_ylim(0.0, 1.05)
    axes.set_ylabel("Rate")
    axes.set_title("Finite CGT Diagnostic Separation")
    for bar, value in zip(bars, values, strict=True):
        axes.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.02,
            f"{value:.2f}",
            ha="center",
            va="bottom",
        )
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    pyplot.close(figure)


def apply_external_analysis(
    *,
    output_dir: Path,
    config: dict[str, Any],
    scenarios: list[dict[str, Any]],
    summary: dict[str, Any],
    metrics: list[dict[str, Any]],
    diagnostic_signatures: dict[str, Any],
) -> dict[str, Any]:
    """Enrich public artifacts with optional experiment-library outputs."""
    summary["analysis_backend"] = "external"
    metrics_summary = build_metrics_summary(metrics)
    summary["rate_confidence_intervals"] = build_rate_intervals(
        summary=summary,
        metrics=metrics,
    )
    summary["external_analysis"] = {
        "libraries": ["pandas", "scipy", "matplotlib", "jsonschema"],
        "metrics_summary_path": "metrics_summary.json",
        "separation_plot_path": "separation_rates.png",
    }
    validate_json_contracts(
        config=config,
        scenarios=scenarios,
        summary=summary,
        metrics=metrics,
        diagnostic_signatures=diagnostic_signatures,
    )
    write_json(output_dir / "metrics_summary.json", metrics_summary)
    write_separation_plot(output_dir / "separation_rates.png", summary)
    return {"metrics_summary": metrics_summary}


def _interval_from_rows(
    stats: Any,
    *,
    rows: list[dict[str, Any]],
    field: str,
    confidence_level: float,
) -> dict[str, Any]:
    trials = len(rows)
    successes = sum(1 for row in rows if _truthy(row.get(field)))
    return _binomial_interval(
        stats,
        successes=successes,
        trials=trials,
        confidence_level=confidence_level,
    )


def _binomial_interval(
    stats: Any,
    *,
    successes: int,
    trials: int,
    confidence_level: float,
) -> dict[str, Any]:
    if trials <= 0:
        return {
            "successes": successes,
            "trials": trials,
            "rate": None,
            "confidence_level": confidence_level,
            "low": None,
            "high": None,
        }
    result = stats.binomtest(successes, trials)
    interval = result.proportion_ci(confidence_level=confidence_level)
    return {
        "successes": successes,
        "trials": trials,
        "rate": successes / trials,
        "confidence_level": confidence_level,
        "low": float(interval.low),
        "high": float(interval.high),
    }


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return False


def _json_clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_clean(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_clean(item) for item in value]
    if hasattr(value, "item"):
        return _json_clean(value.item())
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def public_hash(value: object) -> str:
    """Return a stable hash for external artifact metadata."""
    return stable_hash(value)
