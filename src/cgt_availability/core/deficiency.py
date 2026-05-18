"""Deficiency records and templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

from cgt_availability.core.serialization import (
    JSONValue,
    ensure_json_object,
    json_dumps,
    json_loads_object,
    string_dict,
    string_tuple,
)

Severity = Literal["info", "warning", "blocking"]


class DeficiencyCode(StrEnum):
    """Stable deficiency-code registry for serialization and cross-language ports."""

    MISSING_FRAME = "missing_frame"
    MISSING_SYSTEM = "missing_system"
    MISSING_PROJECTION = "missing_projection"
    MISSING_OBSERVATION = "missing_observation"
    MISSING_DESCRIPTION = "missing_description"
    MISSING_NORMALIZER = "missing_normalizer"
    MISSING_EXPECTED_REPORT = "missing_expected_report"
    MISSING_VERIFIER = "missing_verifier"
    MISSING_FAILURE_PREDICATE = "missing_failure_predicate"
    MISSING_REPRODUCTION_PROTOCOL = "missing_reproduction_protocol"
    MISSING_COMPARISON_REGIME = "missing_comparison_regime"
    MISSING_PROVENANCE = "missing_provenance"
    MISSING_HISTORY = "missing_history"
    MISSING_MARKER_POLICY = "missing_marker_policy"
    MISSING_MARKER_PROVENANCE = "missing_marker_provenance"
    MARKER_POLICY_INCOMPLETE = "marker_policy_incomplete"
    MISSING_CONTINUATION = "missing_continuation"
    MISSING_CONTINUATION_DIAGNOSTIC = "missing_continuation_diagnostic"
    VERIFIER_FAILURE_INCOHERENT = "verifier_failure_incoherent"
    REPORT_PATH_TYPE_ERROR = "report_path_type_error"
    PROTOCOL_INCOHERENT = "protocol_incoherent"
    DIRECT_SELECTOR_DEGENERACY_RISK = "direct_selector_degeneracy_risk"
    REPORT_ONLY_INSUFFICIENCY_RISK = "report_only_insufficiency_risk"
    MARKER_SENSITIVE_MISSING_MARKER_POLICY = "marker_sensitive_missing_marker_policy"
    CONTINUATION_SENSITIVE_MISSING_CONTINUATION = (
        "continuation_sensitive_missing_continuation"
    )


@dataclass(frozen=True)
class DeficiencyCodeInfo:
    """Portable registry metadata for one stable deficiency code."""

    code: str
    group: str
    rationale: str

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class Deficiency:
    """A missing, malformed, incoherent, or risky package component."""

    code: str
    component: str
    severity: Severity
    message: str
    depends_on: tuple[str, ...] = ()
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(
            (
                self.code,
                self.component,
                self.severity,
                self.message,
                self.depends_on,
                json_dumps(self.metadata),
            )
        )

    def sort_key(self) -> tuple[int, str, str, str]:
        severity_order = {"blocking": 0, "warning": 1, "info": 2}
        return (severity_order[self.severity], self.code, self.component, json_dumps(self.metadata))

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Deficiency:
        severity = str(data.get("severity", "warning"))
        if severity not in {"info", "warning", "blocking"}:
            raise ValueError(f"Unknown severity: {severity}")
        return cls(
            code=str(data["code"]),
            component=str(data["component"]),
            severity=severity,  # type: ignore[arg-type]
            message=str(data["message"]),
            depends_on=string_tuple(data.get("depends_on", ())),
            metadata=string_dict(data.get("metadata", {})),
        )

    def to_json(self, *, indent: int | None = None) -> str:
        return json_dumps(self, indent=indent)

    @classmethod
    def from_json(cls, data: str) -> Deficiency:
        return cls.from_dict(json_loads_object(data))


DEFICIENCY_TEMPLATES: dict[str, tuple[str, Severity, str]] = {
    "missing_frame": ("frame", "blocking", "No declared CGT frame is available."),
    "missing_system": ("system", "blocking", "No declared claim-producing system is available."),
    "missing_projection": (
        "projection",
        "blocking",
        "No selected effect projection is declared.",
    ),
    "missing_observation": (
        "observation",
        "blocking",
        "No observation constraint is declared for the selected projection.",
    ),
    "missing_description": (
        "description",
        "blocking",
        "No description constraint is declared for observed effects.",
    ),
    "missing_normalizer": (
        "normalizer",
        "blocking",
        "No normalizer is declared for comparable reports.",
    ),
    "missing_expected_report": (
        "expected_report",
        "blocking",
        "No expected report class is declared.",
    ),
    "missing_verifier": ("verifier", "blocking", "No verifier is declared."),
    "missing_failure_predicate": (
        "failure_predicate",
        "blocking",
        "No operational failure predicate is declared.",
    ),
    "missing_reproduction_protocol": (
        "reproduction_protocol",
        "blocking",
        "No reproduction protocol is declared.",
    ),
    "missing_comparison_regime": (
        "comparison_regime",
        "blocking",
        "A comparison-sensitive claim lacks a declared comparison regime.",
    ),
    "missing_provenance": (
        "provenance",
        "warning",
        "No provenance reference is declared.",
    ),
    "missing_history": (
        "history",
        "blocking",
        "A history-sensitive diagnostic lacks declared construction history.",
    ),
    "missing_marker_policy": (
        "marker_policy",
        "blocking",
        "A marker-sensitive diagnostic lacks a marker policy.",
    ),
    "missing_marker_provenance": (
        "marker_policy",
        "blocking",
        "A marker-sensitive diagnostic lacks declared marker provenance.",
    ),
    "marker_policy_incomplete": (
        "marker_policy",
        "warning",
        "A marker policy is declared but does not preserve unresolved marker information.",
    ),
    "missing_continuation": (
        "continuation",
        "blocking",
        "A continuation-sensitive diagnostic lacks a continuation component.",
    ),
    "missing_continuation_diagnostic": (
        "continuation",
        "blocking",
        "A continuation-sensitive package lacks a residual diagnostic name.",
    ),
    "verifier_failure_incoherent": (
        "verifier",
        "blocking",
        "Declared failure does not imply the verifier's fail verdict.",
    ),
    "report_path_type_error": (
        "report_path",
        "blocking",
        "Declared report-path domains and codomains are incompatible.",
    ),
    "protocol_incoherent": (
        "reproduction_protocol",
        "blocking",
        "The reproduction protocol does not reconstruct the declared report path.",
    ),
    "direct_selector_degeneracy_risk": (
        "degeneracy_control",
        "warning",
        "Direct-selector or unrestricted-selector risk lacks declared controls.",
    ),
    "report_only_insufficiency_risk": (
        "projection",
        "warning",
        "A requested diagnostic dimension is omitted by the report projection.",
    ),
    "marker_sensitive_missing_marker_policy": (
        "marker_policy",
        "blocking",
        "Marker-sensitive availability cannot be diagnosed without marker policy.",
    ),
    "continuation_sensitive_missing_continuation": (
        "continuation",
        "blocking",
        "Continuation-sensitive availability cannot be diagnosed without continuation data.",
    ),
}


DEFICIENCY_CODE_INFO: dict[str, DeficiencyCodeInfo] = {
    "missing_frame": DeficiencyCodeInfo(
        "missing_frame", "formation", "A claim needs a declared frame to type effects."
    ),
    "missing_system": DeficiencyCodeInfo(
        "missing_system", "formation", "The claim-producing system is not declared."
    ),
    "missing_projection": DeficiencyCodeInfo(
        "missing_projection", "formation", "No selected effect can be observed or verified."
    ),
    "missing_observation": DeficiencyCodeInfo(
        "missing_observation", "access", "Selected effects lack an observation constraint."
    ),
    "missing_description": DeficiencyCodeInfo(
        "missing_description", "access", "Observed effects lack a description constraint."
    ),
    "missing_normalizer": DeficiencyCodeInfo(
        "missing_normalizer", "access", "Reports cannot be compared without normalization."
    ),
    "missing_expected_report": DeficiencyCodeInfo(
        "missing_expected_report", "evaluation", "The verifier has no expected report class."
    ),
    "missing_verifier": DeficiencyCodeInfo(
        "missing_verifier", "evaluation", "No declared rule reads the normalized report."
    ),
    "missing_failure_predicate": DeficiencyCodeInfo(
        "missing_failure_predicate", "evaluation", "No finite operational failure condition exists."
    ),
    "missing_reproduction_protocol": DeficiencyCodeInfo(
        "missing_reproduction_protocol", "reproduction", "The report path cannot be replayed."
    ),
    "missing_comparison_regime": DeficiencyCodeInfo(
        "missing_comparison_regime", "formation", "A comparative claim lacks comparison semantics."
    ),
    "missing_provenance": DeficiencyCodeInfo(
        "missing_provenance",
        "reproduction",
        "Data, code, protocol, or source provenance is absent.",
    ),
    "missing_history": DeficiencyCodeInfo(
        "missing_history", "degeneracy", "History-sensitive diagnostics need construction history."
    ),
    "missing_marker_policy": DeficiencyCodeInfo(
        "missing_marker_policy", "marker", "Marker-sensitive diagnostics need marker policy."
    ),
    "missing_marker_provenance": DeficiencyCodeInfo(
        "missing_marker_provenance", "marker", "Marker information needs provenance."
    ),
    "marker_policy_incomplete": DeficiencyCodeInfo(
        "marker_policy_incomplete", "marker", "Unresolved markers must be tracked and preserved."
    ),
    "missing_continuation": DeficiencyCodeInfo(
        "missing_continuation",
        "continuation",
        "Continuation-sensitive diagnostics need residual data.",
    ),
    "missing_continuation_diagnostic": DeficiencyCodeInfo(
        "missing_continuation_diagnostic",
        "continuation",
        "Residual data needs a declared diagnostic readout.",
    ),
    "verifier_failure_incoherent": DeficiencyCodeInfo(
        "verifier_failure_incoherent",
        "coherence",
        "Declared failure must imply the verifier's fail verdict.",
    ),
    "report_path_type_error": DeficiencyCodeInfo(
        "report_path_type_error", "coherence", "Report-path maps do not compose by type."
    ),
    "protocol_incoherent": DeficiencyCodeInfo(
        "protocol_incoherent",
        "coherence",
        "The reproduction protocol does not regenerate the report path.",
    ),
    "direct_selector_degeneracy_risk": DeficiencyCodeInfo(
        "direct_selector_degeneracy_risk",
        "degeneracy",
        "Direct selector and structured construction are not diagnostically separated.",
    ),
    "report_only_insufficiency_risk": DeficiencyCodeInfo(
        "report_only_insufficiency_risk",
        "projection",
        "A requested diagnostic dimension does not factor through the report.",
    ),
    "marker_sensitive_missing_marker_policy": DeficiencyCodeInfo(
        "marker_sensitive_missing_marker_policy",
        "marker",
        "Marker-sensitive availability cannot be read without marker policy.",
    ),
    "continuation_sensitive_missing_continuation": DeficiencyCodeInfo(
        "continuation_sensitive_missing_continuation",
        "continuation",
        "Continuation-sensitive availability cannot be read without continuation data.",
    ),
}


def deficiency_code_info(code: str) -> DeficiencyCodeInfo:
    """Return stable registry metadata for a deficiency code."""
    return DEFICIENCY_CODE_INFO[code]


def make_deficiency(
    code: str,
    *,
    message: str | None = None,
    depends_on: tuple[str, ...] = (),
    metadata: dict[str, JSONValue] | None = None,
    severity: Severity | None = None,
) -> Deficiency:
    """Create a deficiency from the registry, allowing local detail overrides."""
    component, default_severity, default_message = DEFICIENCY_TEMPLATES[code]
    return Deficiency(
        code=code,
        component=component,
        severity=severity or default_severity,
        message=message or default_message,
        depends_on=depends_on,
        metadata=metadata or {},
    )
