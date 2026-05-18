import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[1]
GPL_DENYLIST = {"gpl", "agpl"}
EXTERNAL_TOOL_DENYLIST = {
    "gemma",
    "ollama",
    "prism",
    "storm",
    "storm-checker",
    "stormpy",
}


def test_core_runtime_has_no_required_dependencies() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["dependencies"] == []


def test_declared_optional_dependency_policy_avoids_gpl_named_packages() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    optional = data["project"].get("optional-dependencies", {})
    declared = " ".join(
        dependency.lower()
        for dependencies in optional.values()
        for dependency in dependencies
    )

    assert not any(term in declared for term in GPL_DENYLIST)


def test_declared_dependencies_do_not_vendor_external_model_checkers() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    optional = data["project"].get("optional-dependencies", {})
    declared = {
        dependency.split(";", maxsplit=1)[0]
        .split("[", maxsplit=1)[0]
        .split(">", maxsplit=1)[0]
        .split("=", maxsplit=1)[0]
        .strip()
        .lower()
        for dependencies in optional.values()
        for dependency in dependencies
    }

    assert declared.isdisjoint(EXTERNAL_TOOL_DENYLIST)


def test_jsonschema_extra_does_not_request_format_extras() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    schema_dependencies = data["project"]["optional-dependencies"]["schema"]

    assert all("jsonschema[" not in dependency for dependency in schema_dependencies)


def test_experiments_extra_is_local_analysis_only() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    experiments = data["project"]["optional-dependencies"]["experiments"]
    declared_names = {
        dependency.split(";", maxsplit=1)[0]
        .split("[", maxsplit=1)[0]
        .split(">", maxsplit=1)[0]
        .split("=", maxsplit=1)[0]
        .strip()
        .lower()
        for dependency in experiments
    }

    assert declared_names == {"pandas", "matplotlib", "scipy", "jsonschema"}
    assert declared_names.isdisjoint(EXTERNAL_TOOL_DENYLIST)
