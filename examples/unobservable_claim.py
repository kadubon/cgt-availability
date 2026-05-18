from cgt_availability import (
    AvailabilityAnalyzer,
    ClaimPackage,
    DescriptionSpec,
    FrameSpec,
    ProjectionSpec,
    SystemSpec,
    render_markdown_report,
)


def main() -> None:
    pkg = ClaimPackage(
        claim_id="unobservable-force",
        statement="An undetectable force compatible with all observations explains the outcome.",
        frame=FrameSpec(id="toy-frame"),
        system=SystemSpec(id="undetectable-force-system"),
        projection=ProjectionSpec(id="force-effect", metadata={"codomain": "latent_force"}),
        description=DescriptionSpec(id="verbal-description"),
    )
    report = AvailabilityAnalyzer.default().analyze(pkg)
    print(render_markdown_report(report))


if __name__ == "__main__":
    main()
