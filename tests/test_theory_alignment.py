import json
from pathlib import Path

from conftest import make_complete_package

from cgt_availability import (
    AvailabilityAnalyzer,
    CoarseAvailabilityClass,
    TheoryImplementationStatus,
    coarse_availability_class,
    default_theory_alignment_report,
)

ROOT = Path(__file__).parents[1]


def test_theory_alignment_report_is_documentation_not_runtime_judgment() -> None:
    report = default_theory_alignment_report()

    assert report.metadata["runtime_judgment"] is False
    assert TheoryImplementationStatus.OUT_OF_SCOPE in {item.status for item in report.items}
    assert any(item.concept == "report-factorization obstruction" for item in report.items)
    assert any(
        item.concept == "nondeterministic may/must/almost-sure availability"
        and item.status == TheoryImplementationStatus.POC_APPROXIMATION
        for item in report.items
    )
    assert any(
        item.concept == "finite probabilistic availability model readout"
        and item.status == TheoryImplementationStatus.POC_APPROXIMATION
        for item in report.items
    )
    assert any(
        item.concept == "finite statistical verifier readout"
        and item.status == TheoryImplementationStatus.POC_APPROXIMATION
        for item in report.items
    )
    assert any(
        item.concept == "external statistical and model-checking tools"
        and item.status == TheoryImplementationStatus.ADAPTER_BOUNDARY
        for item in report.items
    )


def test_theory_alignment_fixture_stays_in_sync() -> None:
    fixture = json.loads(
        (ROOT / "fixtures" / "theory_alignment.json").read_text(encoding="utf-8")
    )

    assert default_theory_alignment_report().to_dict() == fixture


def test_theory_audit_document_mentions_all_fixture_concepts() -> None:
    fixture = json.loads(
        (ROOT / "fixtures" / "theory_alignment.json").read_text(encoding="utf-8")
    )
    audit = (ROOT / "docs" / "theory_audit.md").read_text(encoding="utf-8")

    for item in fixture["items"]:
        assert item["concept"] in audit


def test_coarse_availability_class_is_secondary_summary() -> None:
    availability_report = AvailabilityAnalyzer.default().analyze(make_complete_package())

    assert coarse_availability_class(availability_report) == (
        CoarseAvailabilityClass.A8_SCIENTIFICALLY_AVAILABLE
    )
    assert availability_report.metadata["coarse_availability_class"] == "A8"
