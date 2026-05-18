"""Markdown rendering for availability reports."""

from __future__ import annotations

from collections.abc import Sequence

from cgt_availability.core.deficiency import Deficiency
from cgt_availability.core.report import AvailabilityReport


def render_markdown_report(report: AvailabilityReport) -> str:
    lines = [
        f"# Availability report: {report.claim_id}",
        "",
        f"**Status:** `{report.status.value}`",
        "",
        report.summary,
        "",
        "## Layered profile",
        "",
        f"- partial: `{report.profile.is_partial}`",
        f"- complete: `{report.profile.is_complete}`",
        f"- well_typed: `{report.profile.is_well_typed}`",
        f"- coherent: `{report.profile.is_coherent}`",
        f"- reproducibly_available: `{report.profile.is_reproducibly_available}`",
        f"- continuation_sensitive: `{report.profile.is_continuation_sensitive}`",
        f"- blocked: `{report.profile.is_blocked}`",
        "",
    ]
    lines.extend(_render_deficiency_table("Direct deficiencies", report.deficiencies))
    lines.extend(
        _render_deficiency_table(
            "Dependency-closed deficiencies", report.dependency_closed_deficiencies
        )
    )
    if report.warnings:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report.warnings)
        lines.append("")
    if report.recommendations:
        lines.extend(["## Recommendations", ""])
        lines.extend(f"- {recommendation}" for recommendation in report.recommendations)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_deficiency_table(title: str, deficiencies: Sequence[Deficiency]) -> list[str]:
    if not deficiencies:
        return [f"## {title}", "", "No deficiencies reported.", ""]
    rows = [
        f"## {title}",
        "",
        "| Code | Severity | Component | Message |",
        "| --- | --- | --- | --- |",
    ]
    for deficiency in deficiencies:
        code = deficiency.code
        severity = deficiency.severity
        component = deficiency.component
        message = str(deficiency.message).replace("|", "\\|")
        rows.append(f"| `{code}` | `{severity}` | `{component}` | {message} |")
    rows.append("")
    return rows
