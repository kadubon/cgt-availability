# API Stability

`cgt-availability` v0.1.0 is an alpha release. The portable diagnostic contract
is intended to be stable enough for early use and other-language ports, while
research helpers may evolve as the implementation grows.

## Stable v0.1.0 Surface

The stable surface is the part recommended for ordinary scientific availability
diagnostics:

- `ClaimPackage`
- core spec dataclasses: `FrameSpec`, `SystemSpec`, `ProjectionSpec`,
  `ObservationSpec`, `DescriptionSpec`, `NormalizerSpec`,
  `ExpectedReportSpec`, `VerifierSpec`, `FailurePredicateSpec`,
  `ReproductionProtocolSpec`, `ComparisonRegimeSpec`, `HistorySpec`,
  `ContinuationSpec`, `MarkerPolicySpec`, `MarkerStateSpec`,
  `DegeneracyControlSpec`, and `ProvenanceRef`
- `Deficiency`
- `AvailabilityAnalyzer`
- `AvailabilityReport`
- `AvailabilityStatus`
- `AvailabilityProfile`
- `AvailabilityPipeline.minimal()` and `AvailabilityPipeline.standard()`
- `render_markdown_report`
- `render_json_report`

Stable means these names, basic dataclass fields, deficiency codes, status
values, and JSON schema shapes should not change casually in the `0.1.x` line.
It does not mean no new optional fields or helper functions will be added.

## Research And Experimental Surface

The following APIs are useful but less stable:

- residual transition helpers and bounded residual simulation;
- finite DTMC helpers;
- finite may/must/almost-sure run-family helpers;
- finite fixed-point helpers;
- statistical verifier helpers;
- external model-checking adapter profiles;
- repair-cover and coherent repair solvers;
- experiment utilities under `experiments/`.

These APIs are finite executable fragments or adapter boundaries. They are not
full theorem proving, full statistical inference, full temporal-logic model
checking, or full coalgebraic availability semantics.

## Strict Mode

Normal mode accepts a small number of compatibility shortcuts. Strict mode is
recommended for reproducible claim packages because it requires first-class
typed declarations where applicable.

In v0.1.0, strict mode rejects the legacy
`metadata["reconstructs_report_path"]` shortcut unless the package declares the
explicit `ReproductionProtocolSpec.reconstructs` path. This makes reproduction
requirements visible in the package schema rather than hidden in metadata.

## Portability Contract

For cross-language implementations, treat these as the normative artifacts:

- JSON Schema files in `schemas/`;
- conformance fixtures in `fixtures/conformance/`;
- stable deficiency-code registry in `cgt_availability.core.deficiency`;
- theory alignment fixture in `fixtures/theory_alignment.json`.

Python convenience helpers may grow faster than the portable core, but changes
to schema fields, deficiency codes, status values, and core report fields should
be versioned and documented.
