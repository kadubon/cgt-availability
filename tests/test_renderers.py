from cgt_availability import (
    AvailabilityAnalyzer,
    AvailabilityReport,
    render_json_report,
    render_markdown_report,
)


def test_markdown_rendering_includes_deficiencies_and_recommendations(complete_package) -> None:  # type: ignore[no-untyped-def]
    report = AvailabilityAnalyzer.default().analyze(complete_package)
    rendered = render_markdown_report(report)
    assert "Availability report" in rendered
    assert "Recommendations" not in rendered


def test_report_json_roundtrip(complete_package) -> None:  # type: ignore[no-untyped-def]
    report = AvailabilityAnalyzer.default().analyze(complete_package)
    restored = AvailabilityReport.from_json(render_json_report(report))
    assert restored.claim_id == report.claim_id
    assert restored.status == report.status
