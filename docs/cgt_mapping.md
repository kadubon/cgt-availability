# CGT Mapping

This document maps the supplement's scientific-availability vocabulary to the
portable Python schema. The mapping is diagnostic: it records declared
constraints needed for scientific handling, not claim truth or social
classification.

## Package Tuple

| Paper component | Python declaration | Diagnostic role |
| --- | --- | --- |
| `Frame` | `FrameSpec` | declared CGT frame |
| `C` / system | `SystemSpec` | claim-producing system or constraint system |
| `P` | `ProjectionSpec` | selected effect projection |
| `O` | `ObservationSpec` | observation constraint |
| `D` | `DescriptionSpec` | description constraint |
| `N` | `NormalizerSpec` | normalizer to comparable reports |
| `R*` | `ExpectedReportSpec` | expected report class |
| `V` | `VerifierSpec` | finite verifier and verdict domain |
| `FailPred` | `FailurePredicateSpec` | operational failure predicate |
| `Prot` | `ReproductionProtocolSpec` | report-path replay declaration |
| comparison regime | `ComparisonRegimeSpec` | declared comparison dimensions and relation |
| history | `HistorySpec` | construction or constraint history |
| continuation | `ContinuationSpec` | residual constraints, follow-up tests, refinements, repairs |
| marker policy | `MarkerPolicySpec`, `MarkerStateSpec` | unresolved marker tracking and provenance |
| degeneracy control | `DegeneracyControlSpec` | controls against direct target coding |
| provenance | `ProvenanceRef` | data, code, source, or protocol references |

`ClaimPackage` requires only `claim_id` and `statement` so that missing
declarations remain diagnosable.

## Report Path

`ReportPathSpec` and `TypedMapSpec` provide a finite typed representation of:

```text
effect profile -> projection -> observation -> description -> normalized report
```

Legacy domain/codomain metadata is still accepted as a compatibility layer.
When `report_path` is declared, it takes precedence. Verifier, failure
predicate, and expected-report input domains are checked against the normalizer
output when those domains are declared.

## Reproducibility

`ReproductionProtocolSpec.reconstructs` is the finite implementation of
report-path replay. A reproducibly available package must reconstruct:

- `projection`
- `observation`
- `description`
- `normalizer`
- `verifier`

The older `metadata["reconstructs_report_path"]` flag is compatibility-only.
CLI strict mode rejects that metadata-only form.

## Deficiencies And Preorder

The direct deficiency profile corresponds to primitive deficiencies observed in
the package. The dependency-closed deficiency profile is computed through
`DiagnosticVocabulary` and `DependencyGraph`.

`availability_preorder(pkg1, pkg2)` implements the finite preorder:
`pkg2` is at least as available as `pkg1` when its dependency-closed deficiency
profile is a subset of `pkg1`'s profile.

## Report Factorization, Markers, And Continuation

The report-factorization rule uses declared finite data rather than symbolic
factorization. If a requested diagnostic dimension appears in
`projection.metadata["omits_dimensions"]`, the analyzer emits
`report_only_insufficiency_risk`.

Marker-sensitive diagnostics use declared marker policies and marker state.
Continuation-sensitive diagnostics use declared finite residual constraints,
follow-up tests, refinements, repairs, residual transition systems, and
diagnostic-relative readouts.

The library treats availability as frame-relative. It reports missing,
incoherent, induced, or report-forgotten declarations.
