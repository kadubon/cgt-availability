"""Shared helpers for the isolated Ollama Gemma Level 5 experiment."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from cgt_availability import (
    AvailabilityAnalyzer,
    AvailabilityPipeline,
    ClaimPackage,
    RunPackage,
    almost_sure_available,
    evaluate_run_modes,
)

EXPERIMENT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = EXPERIMENT_DIR / "config.json"
DEFAULT_SCENARIO_PATH = EXPERIMENT_DIR / "scenario_catalog.json"
DEFAULT_RAW_OUTPUT_PATH = EXPERIMENT_DIR / "raw" / "ollama_responses.raw.jsonl"
DEFAULT_RESULTS_DIR = EXPERIMENT_DIR / "results"
DEFAULT_V3_SCENARIO_PATH = EXPERIMENT_DIR / "scenario_catalog_v2.json"
DEFAULT_V3_RESULTS_DIR = DEFAULT_RESULTS_DIR / "v3"
DEFAULT_V4_SCENARIO_PATH = EXPERIMENT_DIR / "scenario_catalog_v4.json"
DEFAULT_V4_RESULTS_DIR = DEFAULT_RESULTS_DIR / "v4"
DEFAULT_ENDPOINT = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "gemma4:e4b"
PROMPT_VERSION = "2026-05-18.level5.synthetic.v2"
V3_PROMPT_VERSION = "2026-05-18.level5.synthetic.v3"
V4_PROMPT_VERSION = "2026-05-18.level5.synthetic.v4"
DEFAULT_EXPERIMENT_ARMS = ("minimal_text", "report_only", "schema_guided_dossier")
SCHEMA_GUIDED_ARMS = {
    "schema_guided_dossier",
    "schema_guided_component_slots",
    "schema_guided_repair",
}
CLAIM_PACKAGE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["claim_package"],
    "properties": {
        "claim_package": {
            "type": "object",
            "required": ["claim_id", "statement"],
            "properties": {
                "claim_id": {"type": "string"},
                "statement": {"type": "string"},
                "frame": {"type": "object"},
                "system": {"type": "object"},
                "projection": {"type": "object"},
                "observation": {"type": "object"},
                "description": {"type": "object"},
                "normalizer": {"type": "object"},
                "expected_report": {"type": "object"},
                "verifier": {"type": "object"},
                "failure_predicate": {"type": "object"},
                "reproduction_protocol": {"type": "object"},
                "history": {"type": "object"},
                "continuation": {"type": "object"},
                "marker_policy": {"type": "object"},
                "marker_state": {"type": "object"},
                "degeneracy_control": {"type": "object"},
                "provenance": {"type": "array"},
                "comparison_regime": {"type": "object"},
                "report_path": {"type": "object"},
                "metadata": {"type": "object"},
            },
            "additionalProperties": False,
        }
    },
    "additionalProperties": False,
}
COMPONENT_SLOTS_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["claim_package", "component_slots"],
    "properties": {
        "claim_package": CLAIM_PACKAGE_JSON_SCHEMA["properties"]["claim_package"],
        "component_slots": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["component", "declared", "evidence"],
                "properties": {
                    "component": {
                        "type": "string",
                        "enum": [
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
                        ],
                    },
                    "declared": {"type": "boolean"},
                    "evidence": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}


class ExperimentError(RuntimeError):
    """Raised for explicit experiment harness failures."""


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_hash(value: object) -> str:
    if isinstance(value, str):
        data = value.encode("utf-8")
    else:
        data = canonical_json(value).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExperimentError(f"Expected JSON object in {path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config = load_json_object(path)
    config.setdefault("model", DEFAULT_MODEL)
    config.setdefault("endpoint", DEFAULT_ENDPOINT)
    config.setdefault("think", False)
    config.setdefault("stream", False)
    config.setdefault("format", "json")
    config.setdefault("prompt_version", PROMPT_VERSION)
    config.setdefault("pipeline", "research")
    config.setdefault("temperature", 0.0)
    config.setdefault("seed_list", [101, 102, 103, 104, 105])
    config.setdefault("timeout_seconds", 120.0)
    return config


def load_scenarios(path: Path = DEFAULT_SCENARIO_PATH) -> list[dict[str, Any]]:
    catalog = load_json_object(path)
    base_scenarios: list[dict[str, Any]] = []
    extends = catalog.get("extends")
    if isinstance(extends, str) and extends:
        base_scenarios = load_scenarios(path.parent / extends)
    scenarios = catalog.get("scenarios")
    if not isinstance(scenarios, list):
        raise ExperimentError("scenario catalog must contain a scenarios list")
    normalized: list[dict[str, Any]] = []
    by_id = {str(scenario.get("id")): scenario for scenario in base_scenarios}
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ExperimentError("each scenario must be a JSON object")
        scenario_dict = dict(scenario)
        parent_id = scenario_dict.pop("extends_scenario", None)
        if parent_id is not None:
            try:
                base = deepcopy(by_id[str(parent_id)])
            except KeyError as exc:
                raise ExperimentError(f"Unknown extended scenario: {parent_id}") from exc
            scenario_dict = _deep_merge(base, scenario_dict)
        package_patch = scenario_dict.pop("gold_claim_package_patch", None)
        if package_patch is not None:
            if not isinstance(package_patch, Mapping):
                raise ExperimentError("gold_claim_package_patch must be an object")
            package = _mapping(scenario_dict.get("gold_claim_package", {}))
            scenario_dict["gold_claim_package"] = _deep_merge(package, dict(package_patch))
        for key in _string_list(scenario_dict.pop("remove_gold_claim_package_keys", ())):
            package = _mapping(scenario_dict.get("gold_claim_package", {}))
            package.pop(key, None)
            scenario_dict["gold_claim_package"] = package
        normalized.append(scenario_dict)
        by_id[str(scenario_dict.get("id"))] = scenario_dict
    if catalog.get("include_base", True):
        return [*base_scenarios, *normalized]
    return normalized


def bool_from_cli(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ExperimentError(f"Cannot parse boolean value: {value!r}")


def build_ollama_payload(
    scenario: Mapping[str, Any],
    config: Mapping[str, Any],
    seed: int,
    *,
    arm_id: str = "minimal_text",
    attempt: int = 1,
    repair_feedback: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic Ollama chat payload with thinking disabled."""
    model = str(config.get("model", DEFAULT_MODEL))
    prompt_version = str(config.get("prompt_version", PROMPT_VERSION))
    statement = str(scenario.get("statement", ""))
    category = str(scenario.get("category", ""))
    scenario_id = str(scenario.get("id", ""))
    extraction_context = _extraction_context_for_arm(
        scenario=scenario,
        arm_id=arm_id,
        repair_feedback=repair_feedback,
    )
    user_content = (
        f"Prompt version: {prompt_version}\n"
        f"Experiment arm: {arm_id}\n"
        f"Repair attempt: {attempt}\n"
        f"Scenario id: {scenario_id}\n"
        f"Scenario category: {category}\n"
        f"Synthetic claim text: {statement}\n"
        f"{extraction_context}\n\n"
        "Return strict JSON only, with no Markdown and no explanatory text. "
        "Use exactly this top-level shape:\n"
        "{\n"
        '  "claim_package": {\n'
        f'    "claim_id": "{scenario_id}",\n'
        f'    "statement": "{statement}",\n'
        '    "metadata": {}\n'
        "  }\n"
        "}\n\n"
        "The value of `claim_package` must be a cgt_availability ClaimPackage "
        "dictionary. The required keys are exactly `claim_id` and `statement`. "
        "Do not use replacement keys such as `claim`, `text`, or `constraints`. "
        "You may add only declared ClaimPackage fields when the synthetic text "
        "explicitly supports them: frame, system, projection, observation, "
        "description, normalizer, expected_report, verifier, failure_predicate, "
        "reproduction_protocol, history, continuation, marker_policy, "
        "marker_state, degeneracy_control, provenance, comparison_regime, "
        "report_path, or metadata. Do not decide whether the claim is true. "
        "Do not classify the claim as science or non-science."
    )
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You extract finite scientific-availability claim packages. "
                    "You do not classify truth or science/non-science status."
                ),
            },
            {"role": "user", "content": user_content},
        ],
        "think": bool(config.get("think", False)),
        "stream": bool(config.get("stream", False)),
        "format": str(config.get("format", "json")),
        "options": {
            "seed": seed,
            "temperature": float(config.get("temperature", 0.0)),
        },
    }
    if arm_id == "schema_guided_component_slots":
        payload["format"] = COMPONENT_SLOTS_JSON_SCHEMA
    elif arm_id in SCHEMA_GUIDED_ARMS or config.get("schema_guided") is True:
        payload["format"] = CLAIM_PACKAGE_JSON_SCHEMA
    findings = prompt_leakage_findings(payload, scenario)
    if findings:
        raise ExperimentError(f"Prompt leakage audit failed: {findings}")
    return payload


def experiment_arms(config: Mapping[str, Any]) -> tuple[str, ...]:
    raw = config.get("arms", DEFAULT_EXPERIMENT_ARMS)
    if isinstance(raw, str):
        arms = tuple(item.strip() for item in raw.split(",") if item.strip())
    elif isinstance(raw, list | tuple):
        arms = tuple(str(item) for item in raw)
    else:
        raise ExperimentError("config.arms must be a string or sequence")
    if not arms:
        raise ExperimentError("at least one experiment arm must be declared")
    supported = set(DEFAULT_EXPERIMENT_ARMS) | {
        "schema_guided_component_slots",
        "schema_guided_repair",
    }
    unknown = sorted(set(arms) - supported)
    if unknown:
        raise ExperimentError(f"Unknown experiment arms: {unknown}")
    return arms


def prompt_leakage_findings(
    payload: Mapping[str, Any],
    scenario: Mapping[str, Any],
    *,
    expected_signature_hash: str | None = None,
) -> list[str]:
    """Return any gold-answer tokens that appear in the prompt."""
    text = canonical_json(payload.get("messages", ()))
    findings: list[str] = []
    for code in sorted(expected_codes_for_scenario(scenario)):
        if code and code in text:
            findings.append(f"expected_deficiency_code:{code}")
    expected_status = str(scenario.get("expected_status", ""))
    if expected_status and expected_status in text:
        findings.append(f"expected_status:{expected_status}")
    if expected_signature_hash and expected_signature_hash in text:
        findings.append("expected_cgt_diagnostic_signature_hash")
    return findings


def content_from_ollama_response(response: Mapping[str, Any]) -> str:
    message = response.get("message")
    if isinstance(message, Mapping) and isinstance(message.get("content"), str):
        return str(message["content"])
    if isinstance(response.get("content"), str):
        return str(response["content"])
    raise ExperimentError("Ollama response does not contain message.content")


def response_text_to_package(response_text: str) -> dict[str, Any]:
    try:
        value = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ExperimentError("Model response content is not valid JSON") from exc
    if not isinstance(value, dict):
        raise ExperimentError("Model response JSON must be an object")
    candidate = value.get("claim_package", value.get("package", value))
    if not isinstance(candidate, dict):
        raise ExperimentError("Model response does not contain a claim package object")
    if "claim_id" not in candidate or "statement" not in candidate:
        raise ExperimentError("Claim package requires claim_id and statement")
    return candidate


def declared_components_for_package(package_dict: Mapping[str, Any]) -> tuple[str, ...]:
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
    declared: list[str] = []
    for component in components:
        value = package_dict.get(component)
        if value:
            declared.append(component)
    return tuple(declared)


def analyzer_for_pipeline(name: str) -> AvailabilityAnalyzer:
    pipelines = {
        "minimal": AvailabilityPipeline.minimal,
        "standard": AvailabilityPipeline.standard,
        "interop": AvailabilityPipeline.interop,
        "schema": AvailabilityPipeline.schema,
        "finite_theory": AvailabilityPipeline.finite_theory,
        "graph": AvailabilityPipeline.graph,
        "completion": AvailabilityPipeline.completion,
        "research": AvailabilityPipeline.research,
    }
    try:
        return AvailabilityAnalyzer(pipeline=pipelines[name]())
    except KeyError as exc:
        raise ExperimentError(f"Unknown pipeline: {name}") from exc


def analyze_claim_package_dict(
    package_dict: Mapping[str, Any],
    *,
    pipeline_name: str = "research",
) -> dict[str, Any]:
    pkg = ClaimPackage.from_dict(dict(package_dict))
    report = analyzer_for_pipeline(pipeline_name).analyze(pkg)
    return report.to_dict()


def closed_deficiency_codes(report_dict: Mapping[str, Any]) -> set[str]:
    closed = report_dict.get("dependency_closed_deficiencies", ())
    if not isinstance(closed, list | tuple):
        raise ExperimentError("report dependency_closed_deficiencies must be a sequence")
    codes: set[str] = set()
    for item in closed:
        if isinstance(item, Mapping) and isinstance(item.get("code"), str):
            codes.add(str(item["code"]))
    return codes


def report_only_signature(scenario: Mapping[str, Any]) -> dict[str, Any]:
    """Return the baseline signature visible to report/verdict-only procedures."""
    return {
        "report_signature": str(scenario.get("report_signature", "")),
        "verifier_verdict": str(scenario.get("verifier_verdict", "unknown")),
    }


def closed_profile_signature(report_dict: Mapping[str, Any]) -> dict[str, Any]:
    """Return the ordinary availability signature based on closed deficiencies."""
    return {
        "status": str(report_dict.get("status", "")),
        "closed_deficiency_codes": sorted(closed_deficiency_codes(report_dict)),
    }


def cgt_diagnostic_signature(
    *,
    scenario: Mapping[str, Any],
    package_dict: Mapping[str, Any],
    report_dict: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a theory-facing signature with continuation, marker, history, and protocol data."""
    metadata = _mapping(package_dict.get("metadata", {}))
    report_metadata = _mapping(report_dict.get("metadata", {}))
    continuation = _mapping(package_dict.get("continuation", {}))
    marker_policy = _mapping(package_dict.get("marker_policy", {}))
    marker_state = _mapping(package_dict.get("marker_state", {}))
    history = _mapping(package_dict.get("history", {}))
    protocol = _mapping(package_dict.get("reproduction_protocol", {}))
    reconstructs = _string_list(protocol.get("reconstructs", ()))
    required_reconstructs = {"projection", "observation", "description", "normalizer", "verifier"}
    construction_kind = history.get("construction_kind")
    return {
        "report_only": report_only_signature(scenario),
        "closed_profile": closed_profile_signature(report_dict),
        "requested_dimensions": sorted(_string_list(metadata.get("diagnostics_requested", ()))),
        "continuation": {
            "diagnostic_name": continuation.get("diagnostic_name"),
            "residual_test_count": int(report_metadata.get("residual_test_count", 0)),
            "residual_refinement_count": int(
                report_metadata.get("residual_refinement_count", 0)
            ),
            "residual_repair_count": int(report_metadata.get("residual_repair_count", 0)),
            "has_residual_scientific_space": bool(
                report_metadata.get("has_residual_scientific_space", False)
            ),
        },
        "marker": {
            "policy_declared": bool(marker_policy.get("declared", bool(marker_policy))),
            "tracks_unresolved": bool(marker_policy.get("tracks_unresolved", False)),
            "preserves_markers": bool(
                marker_policy.get("preserves_markers", False)
                or marker_state.get("preserves_markers", False)
            ),
            "marker_provenance_count": len(_string_list(marker_policy.get("marker_provenance", ())))
            + len(_string_list(marker_state.get("marker_provenance", ()))),
            "unresolved_marker_count": len(
                _string_list(marker_state.get("unresolved_markers", ()))
            ),
        },
        "history": {
            "construction_kind": None if construction_kind is None else str(construction_kind),
            "direct_selector": construction_kind == "direct_selector"
            or bool(metadata.get("direct_selector_regime", False)),
        },
        "protocol": {
            "reconstructs": sorted(reconstructs),
            "strict_reconstructs_report_path": required_reconstructs.issubset(reconstructs),
            "legacy_reconstructs_report_path": bool(
                protocol.get("metadata", {}).get("reconstructs_report_path", False)
            )
            if isinstance(protocol.get("metadata", {}), dict)
            else False,
        },
        "run_family": {
            "mode": None
            if metadata.get("run_family_mode") is None
            else str(metadata.get("run_family_mode")),
            "declared_run_count": len(
                _sequence_mappings(_mapping(scenario.get("run_family", {})).get("runs", ()))
            ),
            "has_probabilities": isinstance(
                _mapping(scenario.get("run_family", {})).get("probabilities"),
                Mapping,
            ),
        },
    }


def diagnostic_signature_key(signature: Mapping[str, Any]) -> str:
    """Return a stable key for grouping public diagnostic signatures."""
    return stable_hash(signature)


def evaluate_gold_package(
    scenario: Mapping[str, Any],
    *,
    pipeline_name: str = "research",
) -> dict[str, Any]:
    package_dict = _mapping(scenario.get("gold_claim_package", {}))
    report_dict = analyze_claim_package_dict(package_dict, pipeline_name=pipeline_name)
    cgt_signature = cgt_diagnostic_signature(
        scenario=scenario,
        package_dict=package_dict,
        report_dict=report_dict,
    )
    return {
        "scenario_id": scenario.get("id"),
        "separating_dimension": _focus_dimension(scenario),
        "report_only_signature": report_only_signature(scenario),
        "closed_profile_signature": closed_profile_signature(report_dict),
        "cgt_diagnostic_signature": cgt_signature,
        "cgt_diagnostic_signature_hash": diagnostic_signature_key(cgt_signature),
    }


def evaluate_run_family_spec(
    scenario: Mapping[str, Any],
    *,
    pipeline_name: str = "research",
) -> dict[str, Any] | None:
    run_family = scenario.get("run_family")
    if not isinstance(run_family, Mapping):
        return None
    runs_value = run_family.get("runs", ())
    if not isinstance(runs_value, list | tuple):
        raise ExperimentError("run_family.runs must be a sequence")
    analyzer = analyzer_for_pipeline(pipeline_name)
    base_package = _mapping(scenario.get("gold_claim_package", {}))
    run_packages: list[RunPackage] = []
    for run in runs_value:
        if not isinstance(run, Mapping):
            continue
        package_data = _mapping(run.get("package", {}))
        if not package_data:
            package_data = dict(base_package)
            patch = _mapping(run.get("package_patch", {}))
            package_data.update(patch)
        run_packages.append(
            RunPackage(
                run_id=str(run["run_id"]),
                package=ClaimPackage.from_dict(package_data),
            )
        )
    runs = tuple(run_packages)
    probabilities_raw = run_family.get("probabilities")
    if isinstance(probabilities_raw, Mapping):
        probabilities = {str(key): float(value) for key, value in probabilities_raw.items()}
        result = almost_sure_available(runs, probabilities, analyzer=analyzer)
    else:
        result = evaluate_run_modes(runs, analyzer=analyzer)
    return result.to_dict()


def precision_recall_f1(predicted_codes: set[str], expected_codes: set[str]) -> dict[str, float]:
    true_positive = len(predicted_codes & expected_codes)
    precision = (
        true_positive / len(predicted_codes) if predicted_codes else float(not expected_codes)
    )
    recall = true_positive / len(expected_codes) if expected_codes else float(not predicted_codes)
    if precision + recall == 0.0:
        f1 = 0.0
    else:
        f1 = 2.0 * precision * recall / (precision + recall)
    union = predicted_codes | expected_codes
    jaccard = len(predicted_codes & expected_codes) / len(union) if union else 1.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "jaccard": jaccard,
    }


def expected_codes_for_scenario(scenario: Mapping[str, Any]) -> set[str]:
    value = scenario.get("expected_closed_deficiency_codes", ())
    if not isinstance(value, list | tuple):
        raise ExperimentError("expected_closed_deficiency_codes must be a sequence")
    return {str(item) for item in value}


def public_scenario_projection(scenario: Mapping[str, Any]) -> dict[str, Any]:
    """Return fields safe for public aggregate artifacts."""
    keys = (
        "id",
        "category",
        "report_signature",
        "expected_status",
        "expected_closed_deficiency_codes",
        "expected_cgt_diagnostic_focus",
        "expected_run_modes",
    )
    return {key: scenario[key] for key in keys if key in scenario}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _focus_dimension(scenario: Mapping[str, Any]) -> str | None:
    focus = scenario.get("expected_cgt_diagnostic_focus", {})
    if isinstance(focus, Mapping) and focus.get("separating_dimension") is not None:
        return str(focus["separating_dimension"])
    return None


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value]
    return [str(value)]


def _deep_merge(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(left)
    for key, value in right.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, Mapping)
        ):
            merged[key] = _deep_merge(dict(merged[key]), dict(value))
        else:
            merged[key] = deepcopy(value)
    return merged


def _extraction_context_for_arm(
    *,
    scenario: Mapping[str, Any],
    arm_id: str,
    repair_feedback: str | None,
) -> str:
    report_signature = str(scenario.get("report_signature", ""))
    verifier_verdict = str(scenario.get("verifier_verdict", "unknown"))
    if arm_id == "minimal_text":
        context = "Extraction context: no additional declarations are provided."
    elif arm_id == "report_only":
        context = (
            "Extraction context visible to a report-only procedure:\n"
            f"- report signature: {report_signature}\n"
            f"- verifier verdict: {verifier_verdict}\n"
            "No history, marker, continuation, or protocol reconstruction details "
            "are available in this arm."
        )
    elif arm_id in SCHEMA_GUIDED_ARMS:
        dossier = scenario.get("extraction_dossier")
        if not isinstance(dossier, str) or not dossier.strip():
            dossier = _dossier_from_public_package(_mapping(scenario.get("gold_claim_package", {})))
        if arm_id == "schema_guided_component_slots":
            context = (
                "Extraction dossier with declared availability constraints. Use only "
                "these declarations; do not infer truth or expected deficiency codes.\n"
                f"{dossier.strip()}\n\n"
                "Also return a top-level `component_slots` array. For each "
                "ClaimPackage component, state whether the component is declared "
                "and cite a short evidence phrase from the dossier. The slots are "
                "for extraction auditing only; availability diagnosis still uses "
                "the deterministic analyzer over `claim_package`."
            )
        else:
            context = (
                "Extraction dossier with declared availability constraints. Use only "
                "these declarations; do not infer truth or expected deficiency codes.\n"
                f"{dossier.strip()}"
            )
    else:
        raise ExperimentError(f"Unknown experiment arm: {arm_id}")
    if repair_feedback:
        context += f"\nRepair feedback from schema/analyzer check:\n{repair_feedback}"
    return context


def _dossier_from_public_package(package: Mapping[str, Any]) -> str:
    declared = declared_components_for_package(package)
    lines = [f"- declared components: {', '.join(declared) if declared else 'none'}"]
    for component in declared:
        value = package.get(component)
        if isinstance(value, Mapping):
            component_id = value.get("id")
            if component_id:
                lines.append(f"- {component}: id={component_id}")
        elif component == "provenance" and isinstance(value, list):
            lines.append(f"- provenance count: {len(value)}")
    metadata = _mapping(package.get("metadata", {}))
    requested = _string_list(metadata.get("diagnostics_requested", ()))
    if requested:
        lines.append(f"- requested diagnostic dimensions: {', '.join(requested)}")
    if metadata.get("marker_sensitive") is True:
        lines.append("- marker-sensitive diagnosis is requested")
    if metadata.get("continuation_sensitive") is True:
        lines.append("- continuation-sensitive diagnosis is requested")
    return "\n".join(lines)


def _sequence_mappings(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))
