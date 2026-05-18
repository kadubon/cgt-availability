"""Finite report-factorization witnesses."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from cgt_availability.core.serialization import JSONValue, ensure_json_object, json_dumps


@dataclass(frozen=True)
class EffectProfileRecord:
    """Finite record used to test report-fiber diagnostic separation."""

    id: str
    report: JSONValue
    diagnostic_value: JSONValue
    dimensions: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class FactorizationWitness:
    """Witness that a diagnostic is not report-factorable in a finite sample."""

    diagnostic_name: str
    dimension: str
    report: JSONValue
    left_id: str
    right_id: str
    left_value: JSONValue
    right_value: JSONValue
    omitted_dimension: bool = True
    explanation: str = (
        "Same report has different diagnostic values, so the diagnostic does not "
        "factor through the report on this finite sample."
    )

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


def find_factorization_witness(
    records: Iterable[EffectProfileRecord],
    *,
    dimension: str,
    diagnostic_name: str,
    omitted_dimension: bool = True,
) -> FactorizationWitness | None:
    """Find a finite report-fiber witness for report-only insufficiency."""
    by_report: dict[str, list[EffectProfileRecord]] = {}
    for record in records:
        by_report.setdefault(json_dumps(record.report), []).append(record)
    for bucket in by_report.values():
        ordered = sorted(bucket, key=lambda item: item.id)
        for left_index, left in enumerate(ordered):
            for right in ordered[left_index + 1 :]:
                if json_dumps(left.diagnostic_value) != json_dumps(right.diagnostic_value):
                    return FactorizationWitness(
                        diagnostic_name=diagnostic_name,
                        dimension=dimension,
                        report=left.report,
                        left_id=left.id,
                        right_id=right.id,
                        left_value=left.diagnostic_value,
                        right_value=right.diagnostic_value,
                        omitted_dimension=omitted_dimension,
                    )
    return None
