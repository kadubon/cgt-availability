from __future__ import annotations

import pytest

from cgt_availability import (
    ClaimPackage,
    DescriptionSpec,
    ExpectedReportSpec,
    FailurePredicateSpec,
    FrameSpec,
    NormalizerSpec,
    ObservationSpec,
    ProjectionSpec,
    ProvenanceRef,
    ReproductionProtocolSpec,
    SystemSpec,
    VerifierSpec,
)


def make_complete_package(**overrides: object) -> ClaimPackage:
    data: dict[str, object] = {
        "claim_id": "complete",
        "statement": "A declared finite claim package.",
        "frame": FrameSpec(id="frame"),
        "system": SystemSpec(id="system"),
        "projection": ProjectionSpec(
            id="projection",
            metadata={"domain": "effect_profile", "codomain": "projected"},
        ),
        "observation": ObservationSpec(
            id="observation",
            metadata={"domain": "projected", "codomain": "observed"},
        ),
        "description": DescriptionSpec(
            id="description",
            metadata={"domain": "observed", "codomain": "described"},
        ),
        "normalizer": NormalizerSpec(
            id="normalizer",
            metadata={"domain": "described", "codomain": "report"},
        ),
        "expected_report": ExpectedReportSpec(id="expected"),
        "verifier": VerifierSpec(id="verifier"),
        "failure_predicate": FailurePredicateSpec(id="failure"),
        "reproduction_protocol": ReproductionProtocolSpec(
            id="protocol",
            metadata={"reconstructs_report_path": True},
        ),
        "provenance": (ProvenanceRef(id="source"),),
    }
    data.update(overrides)
    return ClaimPackage(**data)  # type: ignore[arg-type]


@pytest.fixture
def complete_package() -> ClaimPackage:
    return make_complete_package()
