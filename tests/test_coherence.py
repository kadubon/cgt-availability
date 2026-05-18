from dataclasses import replace

from conftest import make_complete_package

from cgt_availability import (
    AvailabilityAnalyzer,
    ExpectedReportSpec,
    FailurePredicateSpec,
    ObservationSpec,
    ReproductionProtocolSpec,
    VerifierSpec,
)


def test_path_type_error_is_detected() -> None:
    pkg = make_complete_package(
        observation=ObservationSpec(
            id="bad-observation",
            metadata={"domain": "wrong-domain", "codomain": "observed"},
        )
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert "report_path_type_error" in {item.code for item in report.deficiencies}


def test_report_consumer_type_error_is_detected() -> None:
    pkg = make_complete_package(
        expected_report=ExpectedReportSpec(
            id="expected",
            metadata={"domain": "wrong-report"},
        )
    )

    report = AvailabilityAnalyzer.default().analyze(pkg)

    assert "report_path_type_error" in {item.code for item in report.deficiencies}


def test_verifier_failure_incoherence_is_detected() -> None:
    pkg = make_complete_package(
        verifier=VerifierSpec(id="verifier", metadata={"verdict": "pass"}),
        failure_predicate=FailurePredicateSpec(
            id="failure",
            metadata={"failure_value": True},
        ),
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    assert "verifier_failure_incoherent" in {item.code for item in report.deficiencies}


def test_protocol_unknown_reference_warns(complete_package) -> None:  # type: ignore[no-untyped-def]
    pkg = replace(
        complete_package,
        reproduction_protocol=ReproductionProtocolSpec(
            id="protocol",
            metadata={"reconstructs_report_path": True, "references": ["unknown"]},
        ),
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    deficiency = next(item for item in report.deficiencies if item.code == "protocol_incoherent")
    assert deficiency.severity == "warning"


def test_empty_reconstructs_protocol_is_incoherent(complete_package) -> None:  # type: ignore[no-untyped-def]
    pkg = replace(
        complete_package,
        reproduction_protocol=ReproductionProtocolSpec(id="protocol"),
    )

    report = AvailabilityAnalyzer.default().analyze(pkg)

    assert "protocol_incoherent" in {item.code for item in report.deficiencies}
    assert not report.profile.is_reproducibly_available


def test_explicit_reconstructs_protocol_is_reproducibly_available(complete_package) -> None:  # type: ignore[no-untyped-def]
    pkg = replace(
        complete_package,
        reproduction_protocol=ReproductionProtocolSpec(
            id="protocol",
            reconstructs=("projection", "observation", "description", "normalizer", "verifier"),
        ),
    )

    report = AvailabilityAnalyzer.default().analyze(pkg)

    assert "protocol_incoherent" not in {item.code for item in report.deficiencies}
    assert report.profile.is_reproducibly_available


def test_verifier_without_fail_verdict_is_incoherent_when_failure_implies_fail(
    complete_package,
) -> None:  # type: ignore[no-untyped-def]
    pkg = replace(
        complete_package,
        verifier=VerifierSpec(id="verifier", verdict_domain=("pass", "inconclusive")),
        failure_predicate=FailurePredicateSpec(id="failure", implies_verifier_fail=True),
    )

    report = AvailabilityAnalyzer.default().analyze(pkg)

    assert "verifier_failure_incoherent" in {item.code for item in report.deficiencies}
