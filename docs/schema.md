# Public Schema

The Python dataclasses are intended to remain easy to port to other languages. Public JSON uses snake_case object fields and string-valued deficiency codes.

The current public schema version is `1.0`. `ClaimPackage` and `AvailabilityReport` serialize `schema_version`; older JSON without the field is read as version `1.0`.

Machine-readable artifacts live in:

- `schemas/claim-package.schema.json`
- `schemas/availability-report.schema.json`
- `schemas/deficiency.schema.json`
- `schemas/deficiency-code-info.schema.json`
- `schemas/residual-simulation-result.schema.json`
- `schemas/continuation-readout.schema.json`
- `schemas/package-patch.schema.json`
- `schemas/repair-candidate-patch.schema.json`
- `schemas/external-model-check-result.schema.json`
- `schemas/adapter-error-record.schema.json`

Cross-language fixtures live in `fixtures/conformance/`.

## Stable Deficiency Codes

The stable code registry is `DeficiencyCode`. Codes are serialized as strings, such as `missing_projection`, `report_path_type_error`, `report_only_insufficiency_risk`, `missing_continuation_diagnostic`, and `marker_policy_incomplete`.

## Claim Package

`ClaimPackage` requires only:

- `claim_id`
- `statement`

All scientific-availability declarations are optional so missing declarations remain diagnosable. First-class declarations include `comparison_regime` and `report_path`; legacy metadata keys remain accepted for compatibility.

## Typed Report Path

`ReportPathSpec` contains typed maps for:

- `projection`
- `observation`
- `description_map`
- `normalizer`

Each map uses `TypedMapSpec.domain` and `TypedMapSpec.codomain`. When `report_path` is declared, it takes precedence over legacy `metadata["domain"]` and `metadata["codomain"]`.

## Availability Report

`AvailabilityReport.status` is a coarse summary. `AvailabilityReport.profile` is the layered readout and should be preferred by downstream tools:

- `is_partial`
- `is_complete`
- `is_well_typed`
- `is_coherent`
- `is_reproducibly_available`
- `is_continuation_sensitive`
- `is_blocked`

## Dependency Vocabulary

`DiagnosticVocabulary` owns a finite `DependencyGraph`. Each `DependencyEdge` has:

- `source`
- `target`
- optional `condition`
- optional `source_component`
- optional `target_component`
- optional `structured_condition`
- optional `activation_condition`
- optional `rationale`

Conditions such as `continuation_sensitive` activate package-relative dependencies only when the package requests that diagnostic dimension.

Structured conditions are preferred for portable implementations:

- `requires_dimension`
- `metadata_equals`
- `component_missing`
- `component_present`
- `component_declared`
- `component_metadata_equals`
- `all_of`
- `any_of`
- `not`

## Compatibility Metadata

The finite compatibility layer still recognizes metadata keys including
`domain`, `codomain`, `comparison_required`, `comparison_regime`,
`diagnostics_requested`, `marker_sensitive`, `continuation_sensitive`, and
`projection.metadata["omits_dimensions"]`.

`reproduction_protocol.metadata["reconstructs_report_path"] = true` is accepted
only as a v0.1 compatibility declaration. Portable packages should declare
`ReproductionProtocolSpec.reconstructs` with `projection`, `observation`,
`description`, `normalizer`, and `verifier`. CLI `--strict` rejects the legacy
metadata-only form.

Each stable deficiency code also has portable registry metadata in
`DEFICIENCY_CODE_INFO`: `code`, `group`, and `rationale`. Other language ports
should preserve these groups for documentation and UI filtering, while treating
the string code as the compatibility key.

## Portability Rule

Other implementations should treat the JSON Schema files and conformance fixtures as the compatibility contract. Python helper behavior may grow faster than the portable core, but changes to schema fields, deficiency codes, or status values should be versioned.
