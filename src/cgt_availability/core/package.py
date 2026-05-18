"""Claim package representation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from cgt_availability.core.schema import SCHEMA_VERSION
from cgt_availability.core.serialization import (
    JSONValue,
    ensure_json_object,
    json_dumps,
    json_loads_object,
    string_dict,
)
from cgt_availability.core.specs import (
    ComparisonRegimeSpec,
    ContinuationSpec,
    DegeneracyControlSpec,
    DescriptionSpec,
    ExpectedReportSpec,
    FailurePredicateSpec,
    FrameSpec,
    HistorySpec,
    MarkerPolicySpec,
    MarkerStateSpec,
    NormalizerSpec,
    ObservationSpec,
    ProjectionSpec,
    ProvenanceRef,
    ReportPathSpec,
    ReproductionProtocolSpec,
    SystemSpec,
    VerifierSpec,
)

SpecType = (
    FrameSpec
    | ComparisonRegimeSpec
    | SystemSpec
    | ProjectionSpec
    | ObservationSpec
    | DescriptionSpec
    | NormalizerSpec
    | ExpectedReportSpec
    | VerifierSpec
    | FailurePredicateSpec
    | ReproductionProtocolSpec
    | HistorySpec
    | ContinuationSpec
    | MarkerPolicySpec
    | MarkerStateSpec
    | DegeneracyControlSpec
    | ReportPathSpec
)


@dataclass
class ClaimPackage:
    """A partial scientific-availability claim package."""

    claim_id: str
    statement: str
    frame: FrameSpec | None = None
    comparison_regime: ComparisonRegimeSpec | None = None
    system: SystemSpec | None = None
    projection: ProjectionSpec | None = None
    observation: ObservationSpec | None = None
    description: DescriptionSpec | None = None
    normalizer: NormalizerSpec | None = None
    report_path: ReportPathSpec | None = None
    expected_report: ExpectedReportSpec | None = None
    verifier: VerifierSpec | None = None
    failure_predicate: FailurePredicateSpec | None = None
    reproduction_protocol: ReproductionProtocolSpec | None = None
    history: HistorySpec | None = None
    continuation: ContinuationSpec | None = None
    marker_policy: MarkerPolicySpec | None = None
    marker_state: MarkerStateSpec | None = None
    degeneracy_control: DegeneracyControlSpec | None = None
    provenance: tuple[ProvenanceRef, ...] = ()
    metadata: dict[str, JSONValue] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    _SPEC_FIELDS: ClassVar[dict[str, type[SpecType]]] = {
        "frame": FrameSpec,
        "comparison_regime": ComparisonRegimeSpec,
        "system": SystemSpec,
        "projection": ProjectionSpec,
        "observation": ObservationSpec,
        "description": DescriptionSpec,
        "normalizer": NormalizerSpec,
        "report_path": ReportPathSpec,
        "expected_report": ExpectedReportSpec,
        "verifier": VerifierSpec,
        "failure_predicate": FailurePredicateSpec,
        "reproduction_protocol": ReproductionProtocolSpec,
        "history": HistorySpec,
        "continuation": ContinuationSpec,
        "marker_policy": MarkerPolicySpec,
        "marker_state": MarkerStateSpec,
        "degeneracy_control": DegeneracyControlSpec,
    }

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClaimPackage:
        kwargs: dict[str, Any] = {
            "claim_id": str(data["claim_id"]),
            "statement": str(data["statement"]),
            "metadata": string_dict(data.get("metadata", {})),
            "schema_version": str(data.get("schema_version", SCHEMA_VERSION)),
        }
        for field_name, spec_cls in cls._SPEC_FIELDS.items():
            value = data.get(field_name)
            kwargs[field_name] = None if value is None else spec_cls.from_dict(value)
        provenance_value = data.get("provenance", ())
        if not isinstance(provenance_value, list | tuple):
            raise TypeError("provenance must be a sequence")
        kwargs["provenance"] = tuple(ProvenanceRef.from_dict(item) for item in provenance_value)
        return cls(**kwargs)

    def to_json(self, *, indent: int | None = None) -> str:
        return json_dumps(self, indent=indent)

    @classmethod
    def from_json(cls, data: str) -> ClaimPackage:
        return cls.from_dict(json_loads_object(data))

    def declared_component_names(self) -> tuple[str, ...]:
        names: list[str] = []
        for field_name in self._SPEC_FIELDS:
            spec = getattr(self, field_name)
            if spec is not None and spec.declared:
                names.append(field_name)
        if self.provenance:
            names.append("provenance")
        return tuple(names)
