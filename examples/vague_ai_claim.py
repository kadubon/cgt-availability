from cgt_availability import AvailabilityAnalyzer, ClaimPackage, render_markdown_report


def main() -> None:
    pkg = ClaimPackage(
        claim_id="vague-ai-claim",
        statement="This AI is smarter than humans.",
        metadata={"comparison_required": True},
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    print(render_markdown_report(report))


if __name__ == "__main__":
    main()
