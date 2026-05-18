"""Generate deterministic synthetic scenario specs for the Level 5 experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import DEFAULT_SCENARIO_PATH, EXPERIMENT_DIR, load_json_object


def prepare_scenarios(
    *,
    catalog_path: Path = DEFAULT_SCENARIO_PATH,
    output_path: Path = EXPERIMENT_DIR / "runs" / "generated_scenarios.json",
) -> dict[str, object]:
    catalog = load_json_object(catalog_path)
    prepared = {
        "source_catalog_hash_note": "Use summarize_results.py for cryptographic hashes.",
        "scenario_version": catalog.get("scenario_version", "unknown"),
        "scenarios": catalog.get("scenarios", []),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(prepared, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return prepared


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=DEFAULT_SCENARIO_PATH)
    parser.add_argument(
        "--output",
        type=Path,
        default=EXPERIMENT_DIR / "runs" / "generated_scenarios.json",
    )
    args = parser.parse_args()
    prepared = prepare_scenarios(catalog_path=args.catalog, output_path=args.output)
    print(f"prepared {len(prepared.get('scenarios', []))} scenarios at {args.output}")


if __name__ == "__main__":
    main()

