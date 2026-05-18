import json
import subprocess
import sys


def _legacy_complete_payload() -> dict[str, object]:
    return {
        "claim_id": "legacy",
        "statement": "Legacy protocol package.",
        "frame": {"id": "frame"},
        "system": {"id": "system"},
        "projection": {"id": "projection", "metadata": {"domain": "effect", "codomain": "p"}},
        "observation": {"id": "observation", "metadata": {"domain": "p", "codomain": "o"}},
        "description": {"id": "description", "metadata": {"domain": "o", "codomain": "d"}},
        "normalizer": {"id": "normalizer", "metadata": {"domain": "d", "codomain": "report"}},
        "expected_report": {"id": "expected"},
        "verifier": {"id": "verifier"},
        "failure_predicate": {"id": "failure"},
        "reproduction_protocol": {
            "id": "protocol",
            "metadata": {"reconstructs_report_path": True},
        },
        "provenance": [{"id": "source"}],
    }


def test_cli_diagnose_json_output(tmp_path) -> None:  # type: ignore[no-untyped-def]
    input_path = tmp_path / "claim.json"
    input_path.write_text(
        json.dumps({"claim_id": "cli", "statement": "A CLI claim."}),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cgt_availability",
            "diagnose",
            str(input_path),
            "--pipeline",
            "interop",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["claim_id"] == "cli"
    assert payload["metadata"]["pipeline"] == "interop"


def test_cli_invalid_claim_package_returns_error(tmp_path) -> None:  # type: ignore[no-untyped-def]
    input_path = tmp_path / "invalid.json"
    input_path.write_text("[]", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "cgt_availability", "diagnose", str(input_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "invalid claim package" in result.stderr


def test_cli_strict_rejects_legacy_protocol_metadata(tmp_path) -> None:  # type: ignore[no-untyped-def]
    input_path = tmp_path / "legacy.json"
    input_path.write_text(json.dumps(_legacy_complete_payload()), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cgt_availability",
            "diagnose",
            str(input_path),
            "--strict",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "strict mode requires" in result.stderr
