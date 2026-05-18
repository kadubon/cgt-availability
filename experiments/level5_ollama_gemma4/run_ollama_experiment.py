"""Run or dry-run the local Ollama Gemma Level 5 experiment."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from common import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_ENDPOINT,
    DEFAULT_MODEL,
    DEFAULT_RAW_OUTPUT_PATH,
    DEFAULT_SCENARIO_PATH,
    ExperimentError,
    bool_from_cli,
    build_ollama_payload,
    canonical_json,
    experiment_arms,
    load_config,
    load_scenarios,
    stable_hash,
)


def call_ollama(
    *,
    endpoint: str,
    payload: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    data = canonical_json(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise ExperimentError(f"Ollama request failed: {exc}") from exc
    try:
        value = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ExperimentError("Ollama returned malformed JSON") from exc
    if not isinstance(value, dict):
        raise ExperimentError("Ollama response must be a JSON object")
    return value


def run_experiment(
    *,
    live: bool,
    config_path: Path,
    scenario_path: Path,
    raw_output_path: Path,
    model: str | None,
    think: bool | None,
    endpoint: str | None,
    max_cases: int | None,
    arms: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    if model is not None:
        config["model"] = model
    if think is not None:
        config["think"] = think
    if endpoint is not None:
        config["endpoint"] = endpoint
    active_arms = arms or experiment_arms(config)
    scenarios = load_scenarios(scenario_path)
    if max_cases is not None:
        scenarios = scenarios[:max_cases]
    seeds = [int(seed) for seed in config.get("seed_list", [101])]
    payload_hashes: list[dict[str, Any]] = []
    records_written = 0

    if live:
        raw_output_path.parent.mkdir(parents=True, exist_ok=True)
        output_file = raw_output_path.open("a", encoding="utf-8")
    else:
        output_file = None

    try:
        for scenario in scenarios:
            for arm_id in active_arms:
                for seed in seeds:
                    payload = build_ollama_payload(
                        scenario,
                        config,
                        seed,
                        arm_id=arm_id,
                    )
                    request_hash = stable_hash(payload)
                    payload_hashes.append(
                        {
                            "scenario_id": scenario.get("id"),
                            "arm_id": arm_id,
                            "seed": seed,
                            "request_hash": request_hash,
                        }
                    )
                    if not live:
                        continue
                    started = time.perf_counter()
                    response = call_ollama(
                        endpoint=str(config.get("endpoint", DEFAULT_ENDPOINT)),
                        payload=payload,
                        timeout_seconds=float(config.get("timeout_seconds", 120.0)),
                    )
                    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 3)
                    raw_record = {
                        "scenario_id": scenario.get("id"),
                        "arm_id": arm_id,
                        "attempt": 1,
                        "seed": seed,
                        "request_hash": request_hash,
                        "response_hash": stable_hash(response),
                        "elapsed_ms": elapsed_ms,
                        "response": response,
                    }
                    assert output_file is not None
                    output_file.write(canonical_json(raw_record) + "\n")
                    output_file.flush()
                    records_written += 1
    finally:
        if output_file is not None:
            output_file.close()

    return {
        "live": live,
        "model": config.get("model", DEFAULT_MODEL),
        "think": config.get("think", False),
        "stream": config.get("stream", False),
        "format": config.get("format", "json"),
        "scenario_count": len(scenarios),
        "arms": list(active_arms),
        "seed_count": len(seeds),
        "payload_hashes": payload_hashes,
        "records_written": records_written,
        "raw_output_path": str(raw_output_path) if live else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="Call local Ollama and write raw output.",
    )
    parser.add_argument("--model", default=None)
    parser.add_argument("--think", default=None)
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIO_PATH)
    parser.add_argument("--raw-output", type=Path, default=DEFAULT_RAW_OUTPUT_PATH)
    parser.add_argument("--endpoint", default=None)
    parser.add_argument(
        "--arms",
        default=None,
        help="Comma-separated experiment arms. Defaults to config.arms.",
    )
    args = parser.parse_args()
    think = None if args.think is None else bool_from_cli(args.think)
    arms = None
    if args.arms is not None:
        arms = tuple(item.strip() for item in args.arms.split(",") if item.strip())
    result = run_experiment(
        live=args.live,
        config_path=args.config,
        scenario_path=args.scenarios,
        raw_output_path=args.raw_output,
        model=args.model,
        think=think,
        endpoint=args.endpoint,
        max_cases=args.max_cases,
        arms=arms,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
