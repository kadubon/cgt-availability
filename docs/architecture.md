# Architecture

`cgt-availability` is organized around a finite, dependency-free diagnostic
core. The central data flow is:

```text
ClaimPackage -> rules -> direct deficiencies -> dependency closure -> AvailabilityReport
```

The analyzer does not decide claim truth. It reports which declared scientific
handling constraints are present, missing, incompatible, induced by dependency,
or forgotten by the report projection.

## Module Boundaries

| Package | Responsibility | Dependency policy |
| --- | --- | --- |
| `core` | dataclasses, serialization, dependency closure, preorder, finite residual helpers, finite repair cover | standard library only |
| `rules` | independent diagnostic rules for required components, typing, coherence, report factorization, marker, continuation, and degeneracy | standard library only |
| `renderers` | Markdown and JSON report rendering | no analysis logic |
| `adapters` | optional SciPy and external-process integration points | lazy imports or user-installed binaries only |
| `experiments` | local research harnesses that may call external tools and summarize redacted outputs | outside core; optional extras only |

`AvailabilityAnalyzer` is a rule runner over an `AvailabilityPipeline`. Rules
implement a small protocol and return `RuleResult`, so new rule packs can be
added without rewriting the analyzer loop.

## Diagnostic Flow

1. Rules produce direct deficiencies and warnings.
2. `DiagnosticVocabulary` supplies a finite `DependencyGraph`.
3. `DependencyClosure` computes package-relative induced deficiencies.
4. `AvailabilityProfile` records layered facts such as complete, well typed,
   coherent, reproducibly available, continuation-sensitive, and blocked.
5. `AvailabilityStatus` and `CoarseAvailabilityClass` provide lossy summaries.

The dependency-closed deficiency profile is the primary diagnostic object.

## Typed Declarations

First-class structured declarations take precedence over compatibility metadata.
`ReportPathSpec` overrides legacy domain/codomain metadata, and
`ComparisonRegimeSpec` overrides metadata comparison declarations. Verifier,
failure-predicate, and expected-report input domains are checked against the
normalizer output when declared.

Reproducible availability requires `ReproductionProtocolSpec.reconstructs` to
cover projection, observation, description, normalization, and verification.
The legacy `metadata["reconstructs_report_path"]` flag is accepted only in
compatibility mode; strict CLI mode rejects it.

## Finite Theory Helpers

Finite witnesses are separate from ordinary analysis. `FactorizationWitness`
and `DirectSelectorWitness` explain report-only insufficiency and selector
degeneracy without changing the report's truth status.

Residual transition systems are finite dataclasses with validation and bounded
label simulation. They are conservative continuation readouts, not temporal
logic model checking.

`evaluate_run_modes`, `almost_sure_available`, `least_fixed_point`, finite DTMC
reachability helpers, and finite binomial verifier helpers implement executable
finite fragments of the paper's nondeterministic, fixed-point, probabilistic,
and statistical vocabulary.

## Adapter Boundary

Optional adapters live outside the analyzer. SciPy-backed helpers import SciPy
only inside adapter functions. PRISM and Storm are not bundled and are not
Python dependencies; adapter profiles only construct and run external commands
installed by the user.

Experiments are one more boundary, not a core layer. The Ollama Gemma Level 5
harness may call a local Ollama service from `experiments/`, but the analyzer
does not import it and public artifacts contain only aggregate metrics and
hashes.

The core does not implement theorem proving, full type theory, general
statistical inference, full temporal-logic model checking, LLM extraction, or
network-backed provenance stores.
