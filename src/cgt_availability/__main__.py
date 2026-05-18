"""Command-line entry point for cgt-availability."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cgt_availability.core.analyzer import AvailabilityAnalyzer
from cgt_availability.core.package import ClaimPackage
from cgt_availability.core.pipeline import AvailabilityPipeline
from cgt_availability.renderers import render_json_report, render_markdown_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m cgt_availability")
    subparsers = parser.add_subparsers(dest="command", required=True)
    diagnose = subparsers.add_parser("diagnose", help="diagnose a ClaimPackage JSON file")
    diagnose.add_argument("input", type=Path)
    diagnose.add_argument(
        "--pipeline",
        choices=(
            "minimal",
            "standard",
            "interop",
            "schema",
            "finite_theory",
            "graph",
            "completion",
            "research",
        ),
        default="standard",
    )
    diagnose.add_argument("--format", choices=("markdown", "json"), default="markdown")
    diagnose.add_argument(
        "--strict",
        action="store_true",
        help="treat legacy compatibility declarations as strict diagnostics",
    )
    args = parser.parse_args(argv)
    if args.command == "diagnose":
        return _diagnose(
            args.input,
            pipeline_name=args.pipeline,
            output_format=args.format,
            strict=args.strict,
        )
    return 2


def _diagnose(path: Path, *, pipeline_name: str, output_format: str, strict: bool = False) -> int:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("input JSON must be an object")
        pkg = ClaimPackage.from_dict(data)
    except Exception as exc:
        print(f"cgt-availability: invalid claim package: {exc}", file=sys.stderr)
        return 1
    if (
        strict
        and pkg.reproduction_protocol is not None
        and pkg.reproduction_protocol.metadata.get("reconstructs_report_path") is True
        and not pkg.reproduction_protocol.reconstructs
    ):
        print(
            "cgt-availability: strict mode requires "
            "ReproductionProtocolSpec.reconstructs instead of legacy "
            "metadata['reconstructs_report_path']",
            file=sys.stderr,
        )
        return 1
    pipeline = _pipeline_for(pipeline_name)
    if strict:
        metadata = dict(pipeline.metadata)
        metadata["strict"] = True
        pipeline = AvailabilityPipeline(
            name=pipeline.name,
            level=pipeline.level,
            rules=pipeline.rules,
            vocabulary=pipeline.vocabulary,
            metadata=metadata,
        )
    analyzer = AvailabilityAnalyzer(pipeline=pipeline)
    report = analyzer.analyze(pkg)
    if output_format == "json":
        print(render_json_report(report))
    else:
        print(render_markdown_report(report), end="")
    return 0


def _pipeline_for(name: str) -> AvailabilityPipeline:
    return {
        "minimal": AvailabilityPipeline.minimal,
        "standard": AvailabilityPipeline.standard,
        "interop": AvailabilityPipeline.interop,
        "schema": AvailabilityPipeline.schema,
        "finite_theory": AvailabilityPipeline.finite_theory,
        "graph": AvailabilityPipeline.graph,
        "completion": AvailabilityPipeline.completion,
        "research": AvailabilityPipeline.research,
    }[name]()


if __name__ == "__main__":
    raise SystemExit(main())
