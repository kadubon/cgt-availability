# cgt-availability v0.1.0: Scientific Availability Diagnostics for CGT Claim Packages

`cgt-availability` is a finite diagnostic library for checking whether
scientific claim packages declare the constraints needed for reproducible
scientific handling. It returns deficiency profiles, dependency-closed
diagnostics, and recommendations rather than truth or science/non-science
judgments.

## What Problem This Solves

Scientific reports, benchmark scores, and verifier verdicts are projections of
richer effect profiles. The same report or verifier verdict can still differ in
observation, description, normalization, verification, failure predicates,
reproduction protocols, comparison regimes, provenance, history, marker policy,
degeneracy controls, and continuation structure.

This release provides a finite CGT diagnostic implementation for asking whether
a claim package declares those handling constraints.

## Included In v0.1.0

- `ClaimPackage` data model and core spec dataclasses.
- `AvailabilityAnalyzer` with staged `AvailabilityPipeline` presets.
- Direct and dependency-closed deficiency profiles.
- Report-path type checks.
- Verifier/failure coherence checks.
- Reproduction protocol checks.
- Report-only insufficiency diagnostics.
- Direct-selector degeneracy warnings.
- Marker-sensitive diagnostics.
- Continuation-sensitive diagnostics.
- Residual transition helpers.
- Finite may/must/almost-sure run-family helpers.
- Finite fixed-point and finite DTMC helpers.
- Finite repair-cover helpers.
- Markdown and JSON renderers.
- CLI diagnosis.
- Examples, fixtures, JSON Schema artifacts, and conformance tests.
- Optional local experiment harness with redacted public artifacts.

## What This Is Not

- Not a truth oracle.
- Not a science/non-science judge.
- Not a full model checker.
- Not a theorem prover.
- Not a statistical inference engine.
- Not an LLM service.
- Not a peer-review replacement.
- Not a full implementation of infinitary, coinductive, or coalgebraic CGT
  availability.
- Optional experiments are not benchmarks and do not validate CGT as a whole.

## Installation And Quickstart

```bash
uv sync
uv run python examples/vague_ai_claim.py
uv run python -m cgt_availability diagnose fixtures/conformance/minimal_claim_package.json
```

Strict mode is recommended for reproducible claim packages:

```bash
uv run python -m cgt_availability diagnose fixtures/conformance/strict_protocol_claim_package.json --pipeline standard --format json --strict
```

## License And Dependency Boundary

The repository is Apache-2.0 licensed and intentionally has no required runtime
dependency outside the Python standard library. Optional dependencies are
installed only through extras and are not bundled. PRISM, Storm, Ollama, and
Gemma models are not vendored and are not Python dependencies.

This repository intentionally uses `LICENSE` only and does not include a
`NOTICE` file.

## Known Limitations

- Alpha API.
- Finite deterministic core.
- Type checking is finite declared domain/codomain compatibility, not full type
  theory.
- Residual simulation helpers are finite bounded diagnostics, not full
  coalgebraic or bisimulation semantics.
- Model-checking adapters are external-process boundaries, not an embedded
  model checker.
- Statistical helpers provide finite readouts, not general statistical
  inference.
- Infinitary and coinductive availability remain roadmap items.

## Citation

Takahashi, K. (2026). *Constraint Generative Theory: Typed Constraint Effects
and Scientific Availability*. Zenodo. https://doi.org/10.5281/zenodo.20262492

## GitHub Release Body

### Summary

`cgt-availability` v0.1.0 is an alpha release of a finite diagnostic library for
scientific availability diagnostics over CGT claim packages. It checks whether a
claim package declares the constraints needed for reproducible scientific
handling and returns a deficiency profile, dependency-closed diagnostics, and
recommendations.

### What It Helps With

The library is useful for claim package diagnostics in scientific workflows,
including reproducible claims, AI benchmark claims, and other settings where a
report projection or verifier verdict should not be confused with the full
effect profile. It asks what is declared, what is missing, what is
type-incoherent, and which report-only, marker-sensitive, history-sensitive,
degeneracy-sensitive, or continuation-sensitive diagnostics need more
structure.

### Included

- Claim package schema and standard-library dataclasses.
- Finite `AvailabilityAnalyzer` pipelines.
- Deficiency profiles and dependency closure.
- Report-path typing and coherence checks.
- Reproduction protocol checks.
- Report-only insufficiency diagnostics.
- Marker, history, continuation, and direct-selector diagnostics.
- Repair-cover helpers.
- Markdown/JSON renderers and CLI diagnosis.
- JSON Schema, fixtures, examples, and tests.
- Optional local experiment harness with redacted aggregate results.

### Not Included

This release does not decide whether a claim is true. It does not judge whether
a claim is science or non-science. It is not a full model checker, theorem
prover, statistical inference engine, LLM service, or peer-review replacement.
Optional experiments are local extraction studies, not benchmarks.

### Quickstart

```bash
uv sync
uv run python examples/vague_ai_claim.py
uv run python -m cgt_availability diagnose fixtures/conformance/minimal_claim_package.json
```

### Theory Source

Takahashi, K. (2026). *Constraint Generative Theory: Typed Constraint Effects
and Scientific Availability*. Zenodo. https://doi.org/10.5281/zenodo.20262492

### Next Steps

The next release should focus on stabilization: schema compatibility,
documentation cleanup, more conformance fixtures, and clearer plugin boundaries
before adding broader theory modules.

## Zenodo-Style Description

**Title:** cgt-availability: Scientific Availability Diagnostics for Constraint
Generative Theory Claim Packages

`cgt-availability` is an Apache-2.0 Python library for finite scientific
availability diagnostics over Constraint Generative Theory (CGT) claim
packages. It checks whether a claim package declares the operational constraints
needed for scientific handling: observation, description, normalization,
verification, failure predicates, reproduction protocols, comparison regimes,
provenance, marker policy, history, degeneracy controls, and continuation
structure.

The library is based on the CGT idea that a report is only a projection of a
richer effect profile. The same report or verifier verdict does not imply the
same scientific availability or the same downstream scientific usefulness.
Accordingly, `cgt-availability` returns deficiency profiles,
dependency-closed diagnostics, coarse availability summaries, and
recommendations rather than truth judgments or science/non-science
demarcation judgments.

Version 0.1.0 is an alpha release with a finite deterministic core, JSON schema
artifacts, examples, tests, documentation, optional finite research helpers, and
a local redacted experiment harness. It is not a theorem prover, full model
checker, general statistical inference engine, LLM service, or peer-review
replacement.

**Keywords:** scientific availability; Constraint Generative Theory; CGT;
reproducibility; scientific claim diagnostics; claim package; effect profile;
report projection; deficiency profile; AI evaluation; benchmark diagnostics;
open science; Python; uv.
