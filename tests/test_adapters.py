import sys

import pytest

from cgt_availability.adapters import (
    PRISM_COMMAND_PROFILE,
    STORM_COMMAND_PROFILE,
    AdapterErrorRecord,
    AdapterExecutionError,
    AdapterUnavailable,
    ExternalModelCheckerAdapter,
    scipy_binomial_verifier,
)
from cgt_availability.core.statistics import BernoulliEvidence


def test_external_model_checker_unavailable_fails_clearly() -> None:
    adapter = ExternalModelCheckerAdapter("definitely-missing-cgt-model-checker")

    with pytest.raises(AdapterUnavailable):
        adapter.check_model("model.pm")


def test_external_model_checker_successful_json_output(tmp_path) -> None:  # type: ignore[no-untyped-def]
    script = tmp_path / "checker.py"
    script.write_text('print("{\\"probability\\": 1.0}")', encoding="utf-8")
    adapter = ExternalModelCheckerAdapter(sys.executable)

    result = adapter.check_model(script, parse_json=True)

    assert result.parsed == {"probability": 1.0}
    assert result.returncode == 0


def test_external_model_checker_execution_error(tmp_path) -> None:  # type: ignore[no-untyped-def]
    script = tmp_path / "checker.py"
    script.write_text("import sys; sys.exit(7)", encoding="utf-8")
    adapter = ExternalModelCheckerAdapter(sys.executable)

    with pytest.raises(AdapterExecutionError):
        adapter.check_model(script)


def test_external_model_checker_parse_failure_is_execution_error(tmp_path) -> None:  # type: ignore[no-untyped-def]
    script = tmp_path / "checker.py"
    script.write_text('print("not-json")', encoding="utf-8")
    adapter = ExternalModelCheckerAdapter(sys.executable)

    with pytest.raises(AdapterExecutionError, match="invalid JSON output"):
        adapter.check_model(script, parse_json=True)


def test_model_checker_command_profiles_build_arguments() -> None:
    assert PRISM_COMMAND_PROFILE.build_arguments("model.pm", "props.pctl") == (
        "model.pm",
        "props.pctl",
    )
    assert STORM_COMMAND_PROFILE.build_arguments(
        "model.pm",
        "P=? [ F done ]",
    ) == ("--prism", "model.pm", "--prop", "P=? [ F done ]")


def test_adapter_error_record_from_exception() -> None:
    record = AdapterErrorRecord.from_exception(
        "prism",
        AdapterUnavailable("missing prism"),
        command=("prism", "model.pm"),
    )

    assert record.to_dict() == {
        "adapter": "prism",
        "error_type": "AdapterUnavailable",
        "message": "missing prism",
        "command": ["prism", "model.pm"],
        "metadata": {},
    }


def test_scipy_adapter_unavailable_fails_clearly(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def missing_import(_name: str) -> object:
        raise ImportError("blocked")

    monkeypatch.setattr("cgt_availability.adapters.statistics.import_module", missing_import)

    with pytest.raises(AdapterUnavailable):
        scipy_binomial_verifier(BernoulliEvidence(successes=1, trials=2), null_probability=0.5)
