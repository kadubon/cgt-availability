"""JSON rendering for availability reports."""

from __future__ import annotations

from cgt_availability.core.report import AvailabilityReport


def render_json_report(report: AvailabilityReport, *, indent: int = 2) -> str:
    return report.to_json(indent=indent)
