from __future__ import annotations

import runpy
from pathlib import Path


def test_examples_run_without_error() -> None:
    root = Path(__file__).resolve().parents[1]
    for name in (
        "vague_ai_claim.py",
        "benchmark_claim.py",
        "unobservable_claim.py",
        "same_report_different_continuation.py",
        "marker_sensitive_claim.py",
    ):
        runpy.run_path(str(root / "examples" / name), run_name="__main__")
