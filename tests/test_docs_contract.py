from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_readme_contains_first_time_user_sections() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    required = (
        "# cgt-availability",
        "## Quickstart",
        "## What it can diagnose",
        "## What it is not",
        "## Pipeline levels",
        "## Optional extras and external tools",
        "## Documentation paths",
        "## License",
    )

    for heading in required:
        assert heading in readme
    assert "does not decide whether a claim is true" in readme
    assert "uv run python -m cgt_availability diagnose" in readme
    assert "AvailabilityAnalyzer.default().analyze(pkg)" in readme
    assert "docs/experiments.md" in readme
    assert "Ollama and Gemma models are also not dependencies" in readme
    assert "--gold-only" in readme


def test_docs_avoid_early_stage_positioning_terms() -> None:
    checked_paths = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
    banned_terms = ("MVP", "PoC", "proof of concept", "future work")

    for path in checked_paths:
        text = path.read_text(encoding="utf-8")
        for term in banned_terms:
            assert term not in text, f"{term!r} remains in {path}"


def test_license_docs_state_no_bundling_and_external_binary_boundary() -> None:
    licenses = (ROOT / "docs" / "licenses.md").read_text(encoding="utf-8")
    dependency_policy = (ROOT / "docs" / "dependency_policy.md").read_text(
        encoding="utf-8"
    )

    assert "Optional dependencies are not bundled" in licenses
    assert "not vendored, bundled, or listed as Python dependencies" in licenses
    assert "Ollama is not bundled or declared as a Python dependency" in licenses
    assert "Do not add `prism`, `storm`," in dependency_policy
    assert "Do not add `ollama`, `gemma`" in dependency_policy
