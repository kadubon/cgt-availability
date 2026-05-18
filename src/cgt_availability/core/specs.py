"""Lightweight serializable spec objects for availability packages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self

from cgt_availability.core.serialization import (
    JSONValue,
    ensure_json_object,
    string_dict,
    string_tuple,
)


@dataclass
class BaseSpec:
    """Common declaration fields shared by package components."""

    id: str
    name: str | None = None
    declared: bool = True
    description: str | None = None
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=str(data["id"]),
            name=None if data.get("name") is None else str(data["name"]),
            declared=bool(data.get("declared", True)),
            description=None if data.get("description") is None else str(data["description"]),
            metadata=string_dict(data.get("metadata", {})),
        )


@dataclass
class FrameSpec(BaseSpec):
    """Declared CGT frame."""


@dataclass
class ComparisonRegimeSpec(BaseSpec):
    """Declared comparison regime for comparative availability claims."""

    dimensions: tuple[str, ...] = ()
    relation: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        base = BaseSpec.from_dict(data)
        return cls(
            id=base.id,
            name=base.name,
            declared=base.declared,
            description=base.description,
            metadata=base.metadata,
            dimensions=string_tuple(data.get("dimensions", ())),
            relation=None if data.get("relation") is None else str(data["relation"]),
        )


@dataclass
class SystemSpec(BaseSpec):
    """Declared claim-producing system or constraint system."""


@dataclass
class ProjectionSpec(BaseSpec):
    """Selected effect projection."""


@dataclass
class ObservationSpec(BaseSpec):
    """Observation constraint or map."""


@dataclass
class DescriptionSpec(BaseSpec):
    """Description constraint or map."""


@dataclass
class NormalizerSpec(BaseSpec):
    """Normalizer from described observations to comparable reports."""


@dataclass
class ExpectedReportSpec(BaseSpec):
    """Expected report class or target report region."""


@dataclass
class TypedMapSpec(BaseSpec):
    """Reusable finite domain/codomain declaration for report-path components."""

    domain: str | None = None
    codomain: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        base = BaseSpec.from_dict(data)
        return cls(
            id=base.id,
            name=base.name,
            declared=base.declared,
            description=base.description,
            metadata=base.metadata,
            domain=None if data.get("domain") is None else str(data["domain"]),
            codomain=None if data.get("codomain") is None else str(data["codomain"]),
        )


@dataclass
class ReportPathSpec(BaseSpec):
    """Typed report path from selected effects to normalized reports."""

    projection: TypedMapSpec | None = None
    observation: TypedMapSpec | None = None
    description_map: TypedMapSpec | None = None
    normalizer: TypedMapSpec | None = None
    verifier_domain: tuple[str, ...] = ()
    failure_domain: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        base = BaseSpec.from_dict(data)
        return cls(
            id=base.id,
            name=base.name,
            declared=base.declared,
            description=base.description,
            metadata=base.metadata,
            projection=_typed_map_from_optional(data.get("projection")),
            observation=_typed_map_from_optional(data.get("observation")),
            description_map=_typed_map_from_optional(data.get("description_map")),
            normalizer=_typed_map_from_optional(data.get("normalizer")),
            verifier_domain=string_tuple(data.get("verifier_domain", ())),
            failure_domain=string_tuple(data.get("failure_domain", ())),
        )


@dataclass
class ResidualConstraintSpec(BaseSpec):
    """Typed residual constraint declaration for continuation-sensitive diagnosis."""

    constraint_type: str | None = None
    admissibility_condition: str | None = None
    state: str | None = None
    effect_dimensions: tuple[str, ...] = ()
    comparison_regime: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        base = BaseSpec.from_dict(data)
        return cls(
            id=base.id,
            name=base.name,
            declared=base.declared,
            description=base.description,
            metadata=base.metadata,
            constraint_type=None
            if data.get("constraint_type") is None
            else str(data["constraint_type"]),
            admissibility_condition=None
            if data.get("admissibility_condition") is None
            else str(data["admissibility_condition"]),
            state=None if data.get("state") is None else str(data["state"]),
            effect_dimensions=string_tuple(data.get("effect_dimensions", ())),
            comparison_regime=None
            if data.get("comparison_regime") is None
            else str(data["comparison_regime"]),
        )


@dataclass
class VerifierSpec(BaseSpec):
    """Verifier over normalized reports and expected report classes."""

    verdict_domain: tuple[str, ...] = ("pass", "fail", "inconclusive")
    rule: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        base = BaseSpec.from_dict(data)
        return cls(
            id=base.id,
            name=base.name,
            declared=base.declared,
            description=base.description,
            metadata=base.metadata,
            verdict_domain=string_tuple(
                data.get("verdict_domain", ("pass", "fail", "inconclusive"))
            ),
            rule=None if data.get("rule") is None else str(data["rule"]),
        )


@dataclass
class FailurePredicateSpec(BaseSpec):
    """Operational finite failure predicate."""

    rule: str | None = None
    implies_verifier_fail: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        base = BaseSpec.from_dict(data)
        return cls(
            id=base.id,
            name=base.name,
            declared=base.declared,
            description=base.description,
            metadata=base.metadata,
            rule=None if data.get("rule") is None else str(data["rule"]),
            implies_verifier_fail=bool(data.get("implies_verifier_fail", True)),
        )


@dataclass
class ReproductionProtocolSpec(BaseSpec):
    """Protocol intended to regenerate the declared report path."""

    reconstructs: tuple[str, ...] = ()
    equivalence: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        base = BaseSpec.from_dict(data)
        return cls(
            id=base.id,
            name=base.name,
            declared=base.declared,
            description=base.description,
            metadata=base.metadata,
            reconstructs=string_tuple(data.get("reconstructs", ())),
            equivalence=None if data.get("equivalence") is None else str(data["equivalence"]),
        )


@dataclass
class HistorySpec(BaseSpec):
    """Construction or constraint history."""

    construction_kind: str | None = None
    steps: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        base = BaseSpec.from_dict(data)
        return cls(
            id=base.id,
            name=base.name,
            declared=base.declared,
            description=base.description,
            metadata=base.metadata,
            construction_kind=None
            if data.get("construction_kind") is None
            else str(data["construction_kind"]),
            steps=string_tuple(data.get("steps", ())),
        )


@dataclass
class ContinuationSpec(BaseSpec):
    """Declared residual continuation component."""

    residual_constraints: tuple[str, ...] = ()
    follow_up_tests: tuple[str, ...] = ()
    refinement_paths: tuple[str, ...] = ()
    repair_paths: tuple[str, ...] = ()
    diagnostic_name: str | None = None
    residual_constraint_specs: tuple[ResidualConstraintSpec, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        base = BaseSpec.from_dict(data)
        return cls(
            id=base.id,
            name=base.name,
            declared=base.declared,
            description=base.description,
            metadata=base.metadata,
            residual_constraints=string_tuple(data.get("residual_constraints", ())),
            follow_up_tests=string_tuple(data.get("follow_up_tests", ())),
            refinement_paths=string_tuple(data.get("refinement_paths", ())),
            repair_paths=string_tuple(data.get("repair_paths", ())),
            diagnostic_name=None
            if data.get("diagnostic_name") is None
            else str(data["diagnostic_name"]),
            residual_constraint_specs=tuple(
                ResidualConstraintSpec.from_dict(item)
                for item in _sequence_dicts(data.get("residual_constraint_specs", ()))
            ),
        )


@dataclass
class MarkerPolicySpec(BaseSpec):
    """Marker or inconsistency-policy declaration."""

    tracks_unresolved: bool = False
    marker_provenance: tuple[str, ...] = ()
    preserves_markers: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        base = BaseSpec.from_dict(data)
        return cls(
            id=base.id,
            name=base.name,
            declared=base.declared,
            description=base.description,
            metadata=base.metadata,
            tracks_unresolved=bool(data.get("tracks_unresolved", False)),
            marker_provenance=string_tuple(data.get("marker_provenance", ())),
            preserves_markers=bool(data.get("preserves_markers", False)),
        )


@dataclass
class MarkerStateSpec(BaseSpec):
    """Declared finite marker state for marker-sensitive availability."""

    unresolved_markers: tuple[str, ...] = ()
    marker_provenance: tuple[str, ...] = ()
    preserves_markers: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        base = BaseSpec.from_dict(data)
        return cls(
            id=base.id,
            name=base.name,
            declared=base.declared,
            description=base.description,
            metadata=base.metadata,
            unresolved_markers=string_tuple(data.get("unresolved_markers", ())),
            marker_provenance=string_tuple(data.get("marker_provenance", ())),
            preserves_markers=bool(data.get("preserves_markers", False)),
        )


@dataclass
class DegeneracyControlSpec(BaseSpec):
    """Controls against direct-selector or report-only degeneracy."""

    controls: tuple[str, ...] = ()
    restricted_selector_language: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        base = BaseSpec.from_dict(data)
        return cls(
            id=base.id,
            name=base.name,
            declared=base.declared,
            description=base.description,
            metadata=base.metadata,
            controls=string_tuple(data.get("controls", ())),
            restricted_selector_language=bool(data.get("restricted_selector_language", False)),
        )


@dataclass
class ProvenanceRef(BaseSpec):
    """Reference to provenance, data, code, protocol, or source material."""

    uri: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        base = BaseSpec.from_dict(data)
        return cls(
            id=base.id,
            name=base.name,
            declared=base.declared,
            description=base.description,
            metadata=base.metadata,
            uri=None if data.get("uri") is None else str(data["uri"]),
        )


def _typed_map_from_optional(value: object) -> TypedMapSpec | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TypeError("typed map value must be a mapping")
    return TypedMapSpec.from_dict(value)


def _sequence_dicts(value: object) -> tuple[dict[str, Any], ...]:
    if value is None:
        return ()
    if not isinstance(value, list | tuple):
        raise TypeError("expected a sequence of mappings")
    result: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise TypeError("expected a sequence of mappings")
        result.append(item)
    return tuple(result)
