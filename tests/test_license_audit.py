import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
LICENSE_AUDIT = ROOT / "tools" / "license_audit.py"


def _load_license_audit():
    spec = importlib.util.spec_from_file_location("license_audit", LICENSE_AUDIT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_license_denylist_detects_strong_copyleft_but_not_lgpl_or_mpl() -> None:
    license_audit = _load_license_audit()

    assert license_audit.is_denylisted_license("GNU General Public License v3")
    assert license_audit.is_denylisted_license("AGPL-3.0-only")
    assert not license_audit.is_denylisted_license("LGPL-2.1-only")
    assert not license_audit.is_denylisted_license("MPL-2.0")


def test_license_audit_prefers_permissive_classifier_for_long_notice_metadata() -> None:
    license_audit = _load_license_audit()
    source = license_audit.license_evidence_for_denylist(
        license_value=("BSD terms. " * 120) + "GNU General Public License v3 notice.",
        license_expression="",
        classifiers=("License :: OSI Approved :: BSD License",),
    )

    assert not license_audit.is_denylisted_license(source)


def test_license_audit_cli_emits_json_for_current_package() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(LICENSE_AUDIT),
            "--packages",
            "cgt-availability",
            "--allow-missing",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    report = json.loads(completed.stdout)

    assert report["ok"] is True
    assert report["denylisted"] == []
