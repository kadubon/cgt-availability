"""Compare a local public summary with the published experiment summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import DEFAULT_RESULTS_DIR


def compare_values(actual: Any, expected: Any, *, tolerance: float, path: str = "$") -> list[str]:
    if isinstance(actual, int | float) and isinstance(expected, int | float):
        if abs(float(actual) - float(expected)) <= tolerance:
            return []
        return [f"{path}: {actual!r} differs from {expected!r}"]
    if isinstance(actual, dict) and isinstance(expected, dict):
        errors: list[str] = []
        for key in sorted(set(actual) | set(expected)):
            if key not in actual:
                errors.append(f"{path}.{key}: missing from actual")
            elif key not in expected:
                errors.append(f"{path}.{key}: unexpected in actual")
            else:
                errors.extend(
                    compare_values(
                        actual[key],
                        expected[key],
                        tolerance=tolerance,
                        path=f"{path}.{key}",
                    )
                )
        return errors
    if isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            return [f"{path}: list length {len(actual)} differs from {len(expected)}"]
        errors = []
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected, strict=True)):
            errors.extend(
                compare_values(
                    actual_item,
                    expected_item,
                    tolerance=tolerance,
                    path=f"{path}[{index}]",
                )
            )
        return errors
    if actual != expected:
        return [f"{path}: {actual!r} differs from {expected!r}"]
    return []


def verify_reproduction(
    *,
    actual_path: Path,
    expected_path: Path,
    tolerance: float = 1e-9,
) -> list[str]:
    actual = json.loads(actual_path.read_text(encoding="utf-8"))
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    return compare_values(actual, expected, tolerance=tolerance)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actual", type=Path, default=DEFAULT_RESULTS_DIR / "summary.json")
    parser.add_argument("--expected", type=Path, default=DEFAULT_RESULTS_DIR / "summary.json")
    parser.add_argument("--tolerance", type=float, default=1e-9)
    args = parser.parse_args()
    errors = verify_reproduction(
        actual_path=args.actual,
        expected_path=args.expected,
        tolerance=args.tolerance,
    )
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("reproduction summary matches within tolerance")


if __name__ == "__main__":
    main()

