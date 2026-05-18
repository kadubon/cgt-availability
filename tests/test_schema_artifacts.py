import json
from pathlib import Path

from cgt_availability import (
    DEFICIENCY_CODE_INFO,
    SCHEMA_VERSION,
    STABLE_DEFICIENCY_CODES,
    AvailabilityAnalyzer,
    AvailabilityReport,
    ClaimPackage,
    ContinuationReadout,
    PackagePatch,
    RepairCandidatePatch,
    ResidualSimulationResult,
)
from cgt_availability.adapters import AdapterErrorRecord, ExternalModelCheckResult

ROOT = Path(__file__).parents[1]


def test_schema_artifacts_match_public_code_registry() -> None:
    deficiency_schema = _load_json(ROOT / "schemas" / "deficiency.schema.json")

    assert deficiency_schema["$id"].endswith("/deficiency.schema.json")
    assert tuple(deficiency_schema["properties"]["code"]["enum"]) == STABLE_DEFICIENCY_CODES


def test_claim_package_conformance_fixtures_roundtrip() -> None:
    minimal = _load_json(ROOT / "fixtures" / "conformance" / "minimal_claim_package.json")
    complete = _load_json(ROOT / "fixtures" / "conformance" / "complete_claim_package.json")

    assert ClaimPackage.from_dict(minimal).schema_version == SCHEMA_VERSION
    assert ClaimPackage.from_dict(complete).claim_id == "fixture-complete"


def test_availability_report_conformance_fixture_roundtrip() -> None:
    fixture = _load_json(ROOT / "fixtures" / "conformance" / "availability_report_minimal.json")

    report = AvailabilityReport.from_dict(fixture)

    assert report.schema_version == SCHEMA_VERSION
    assert report.status.value == "unformed"


def test_jsonschema_validation_when_optional_extra_is_installed() -> None:
    try:
        import jsonschema
    except ModuleNotFoundError:
        return

    claim_schema = _load_json(ROOT / "schemas" / "claim-package.schema.json")
    report_schema = _load_json(ROOT / "schemas" / "availability-report.schema.json")
    jsonschema.validate(
        _load_json(ROOT / "fixtures" / "conformance" / "minimal_claim_package.json"),
        claim_schema,
    )
    jsonschema.validate(
        _load_json(ROOT / "fixtures" / "conformance" / "availability_report_minimal.json"),
        report_schema,
    )


def test_new_schema_artifacts_validate_portable_result_objects_when_available() -> None:
    try:
        import jsonschema
    except ModuleNotFoundError:
        return

    deficiency_info_schema = _load_json(
        ROOT / "schemas" / "deficiency-code-info.schema.json"
    )
    residual_schema = _load_json(
        ROOT / "schemas" / "residual-simulation-result.schema.json"
    )
    readout_schema = _load_json(ROOT / "schemas" / "continuation-readout.schema.json")
    package_patch_schema = _load_json(ROOT / "schemas" / "package-patch.schema.json")
    repair_patch_schema = _load_json(
        ROOT / "schemas" / "repair-candidate-patch.schema.json"
    )
    model_check_schema = _load_json(
        ROOT / "schemas" / "external-model-check-result.schema.json"
    )
    adapter_error_schema = _load_json(
        ROOT / "schemas" / "adapter-error-record.schema.json"
    )
    repair_fixture = _load_json(
        ROOT / "fixtures" / "conformance" / "coherent_repair_patch.json"
    )

    for code_info in DEFICIENCY_CODE_INFO.values():
        jsonschema.validate(code_info.to_dict(), deficiency_info_schema)
    jsonschema.validate(
        _load_json(ROOT / "fixtures" / "conformance" / "residual_simulation_result.json"),
        residual_schema,
    )
    jsonschema.validate(
        ResidualSimulationResult(
            source="s0",
            target="t0",
            matched=True,
        ).to_dict(),
        residual_schema,
    )
    jsonschema.validate(
        ContinuationReadout(
            diagnostic_name="utility",
            residual_constraint_count=1,
            follow_up_test_count=1,
            refinement_path_count=0,
            repair_path_count=0,
            has_residual_scientific_space=True,
            required_labels=("probe",),
            missing_labels=(),
            matched_simulation_depth=1,
            utility_metric_name="utility",
        ).to_dict(),
        readout_schema,
    )
    jsonschema.validate(repair_fixture["package_patch"], package_patch_schema)
    jsonschema.validate(repair_fixture["repair_candidate_patch"], repair_patch_schema)
    jsonschema.validate(PackagePatch().to_dict(), package_patch_schema)
    jsonschema.validate(
        RepairCandidatePatch(candidate_id="candidate", patch=PackagePatch()).to_dict(),
        repair_patch_schema,
    )
    jsonschema.validate(
        ExternalModelCheckResult(
            command=("checker", "model.pm"),
            returncode=0,
            stdout="{}",
            stderr="",
            parsed={},
        ).to_dict(),
        model_check_schema,
    )
    jsonschema.validate(
        _load_json(ROOT / "fixtures" / "conformance" / "adapter_failure.json"),
        adapter_error_schema,
    )
    jsonschema.validate(
        AdapterErrorRecord(
            adapter="storm",
            error_type="AdapterUnavailable",
            message="missing",
        ).to_dict(),
        adapter_error_schema,
    )


def test_strict_protocol_and_marker_conformance_fixtures_have_expected_profiles() -> None:
    strict_package = ClaimPackage.from_dict(
        _load_json(ROOT / "fixtures" / "conformance" / "strict_protocol_claim_package.json")
    )
    marker_package = ClaimPackage.from_dict(
        _load_json(ROOT / "fixtures" / "conformance" / "marker_blocking_claim_package.json")
    )
    analyzer = AvailabilityAnalyzer.default()

    strict_report = analyzer.analyze(strict_package)
    marker_report = analyzer.analyze(marker_package)

    assert strict_report.profile.is_reproducibly_available
    assert not marker_report.profile.is_coherent
    assert "marker_policy_incomplete" in {
        item.code for item in marker_report.dependency_closed_deficiencies
    }


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value
