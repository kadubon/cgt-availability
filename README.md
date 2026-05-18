# cgt-availability

`cgt-availability` is a finite diagnostic library for scientific availability
of CGT claim packages. It supports scientific claim diagnostics for
reproducible claims, AI benchmark claims, and scientific workflow diagnostics.

cgt-availability does not decide whether a claim is true. It does not judge
whether a claim is science or non-science. It diagnoses whether a claim has the
declared constraints needed to be handled scientifically: observation,
description, normalization, verification, failure, reproduction, comparison,
provenance, marker policy, history, degeneracy control, and continuation
structure.

The core idea from Constraint Generative Theory (CGT) is simple: a report is
only a report projection of a richer effect profile. Two packages can have the
same report or verifier verdict while differing in what they make observable,
reproducible, repairable, or usable for follow-up scientific work. The library
therefore returns a deficiency profile and recommendations, not a truth or
demarcation judgment.

## Quickstart

Install the local environment and run an example:

```bash
uv sync
uv run python examples/vague_ai_claim.py
```

Run the CLI on a JSON claim package:

```bash
uv run python -m cgt_availability diagnose fixtures/conformance/minimal_claim_package.json
uv run python -m cgt_availability diagnose fixtures/conformance/strict_protocol_claim_package.json --pipeline standard --format json --strict
```

Use the Python API:

```python
from cgt_availability import AvailabilityAnalyzer, ClaimPackage

pkg = ClaimPackage(
    claim_id="vague-ai-claim",
    statement="This AI is smarter than humans.",
    metadata={"comparison_required": True},
)

report = AvailabilityAnalyzer.default().analyze(pkg)
print(report.status)
print([item.code for item in report.dependency_closed_deficiencies])
```

## Core diagnostic output

Every analysis returns an `AvailabilityReport` containing:

- direct deficiencies;
- dependency-closed deficiencies;
- a layered availability profile;
- a coarse status;
- warnings and recommendations;
- metadata describing the pipeline, strict mode, declared components, and finite
  residual readouts.

## What it can diagnose

- **Deficiency profiles:** what is declared, missing, malformed, incoherent, or risky.
- **Dependency closure:** which missing declarations induce further unavailable diagnostics.
- **Typed/coherence issues:** report-path type errors, verifier/failure conflicts, and protocol incoherence.
- **Report-only insufficiency:** requested dimensions that do not factor through the declared report projection.
- **Marker and continuation sensitivity:** marker policy, marker provenance, residual constraints, follow-up tests, refinements, and repairs.
- **Direct-selector degeneracy risk:** cases where direct target coding is not separated from structured construction by declared controls.
- **Repair cover:** finite repair-candidate selection for deficiency coverage.
- **Finite research helpers:** finite may/must/almost-sure run-family checks, finite fixed-point iteration, finite DTMC reachability readouts, and finite binomial verifier readouts.

The primary result is the dependency-closed deficiency profile. The
`AvailabilityStatus` and `CoarseAvailabilityClass` labels are readable summaries,
not social classifications.

## What it is not

- not a truth oracle
- not a science/non-science judge
- not a general statistical inference engine
- not a model checker
- not a theorem prover
- not an LLM service
- not a peer-review replacement
- not a full implementation of every infinitary or coinductive CGT direction

Optional statistical and model-checking adapters return declared readouts or
adapter errors. They do not turn external tool results into truth or demarcation
judgments.

## Pipeline levels

`AvailabilityPipeline` lets users adopt the library in stages while keeping the
same `ClaimPackage -> AvailabilityReport` shape.

| Level | Name | Dependency profile | Use case |
| --- | --- | --- | --- |
| 0 | `minimal` | standard library only | required declarations and dependency closure |
| 1 | `standard` | standard library only | default finite diagnostics and renderers |
| 2 | `interop` / `schema` | optional `schema` extra for validation | JSON Schema, fixtures, CLI integration |
| 3 | `finite_theory` / `graph` | optional graph tooling outside core | finite witnesses and structured dependency metadata |
| 4 | `completion` | optional `opt` extra for large repair problems | repair-cover workflows |
| 5 | `research` | optional `stats`, `modelcheck`, `research`, or `experiments` extras | finite run modes, finite fixed points, residual systems, plugin boundaries, and local redacted experiments |

```python
from cgt_availability import AvailabilityAnalyzer, AvailabilityPipeline, ClaimPackage

pkg = ClaimPackage(claim_id="minimal", statement="An undeclared claim.")
analyzer = AvailabilityAnalyzer(pipeline=AvailabilityPipeline.minimal())
report = analyzer.analyze(pkg)
print([item.code for item in report.dependency_closed_deficiencies])
```

## Core concepts

An availability package is a declared diagnostic presentation of a claim. Only
`claim_id` and `statement` are required at construction time, because missing
declarations are diagnostic targets.

A deficiency profile records missing, malformed, incoherent, or risky
components. The analyzer separates direct deficiencies from dependency-closed
deficiencies, so a missing normalizer can induce unavailable verifier and
failure-predicate diagnostics.

An availability profile records layered facts: partial, complete, well typed,
coherent, reproducibly available, continuation-sensitive, and blocked. The
layered `profile` is the more theory-aligned readout; `status` is a coarse
summary.

Reproducibly available packages must declare that the reproduction protocol
reconstructs the selected projection, observation, description, normalization,
and verification path. Legacy `metadata["reconstructs_report_path"]` remains a
compatibility path, but CLI `--strict` rejects it.

Availability preorder is available through `availability_preorder(pkg1, pkg2)`.
It compares dependency-closed deficiency profiles: `pkg2` is at least as
available as `pkg1` when it has no more closed deficiencies.

## Optional extras and external tools

The core runtime has no required third-party dependencies. Optional libraries are
not bundled; they are installed only when the user selects an extra.

- `schema`: JSON Schema validation with `jsonschema`
- `fast`: serialization adapters with `msgspec`
- `graph` / `modelcheck`: graph-backed finite helpers with `networkx`
- `stats`: statistical verifier acceleration with `scipy`
- `opt`: weighted repair cover with `ortools`
- `adapters`: optional adapter models with `pydantic`
- `test`: property-test tooling with `hypothesis`
- `experiments`: local experiment tables and plots with `pandas`, `matplotlib`,
  `scipy`, and `jsonschema`

PRISM and Storm are not Python dependencies and are not vendored. They are
supported only through external-process adapter profiles configured by the user.
Ollama and Gemma models are also not dependencies and are not bundled.

## API stability in v0.1.0

The stable v0.1.0 surface is intentionally small:

- `ClaimPackage`
- core spec dataclasses such as `FrameSpec`, `ProjectionSpec`, `VerifierSpec`,
  `ReproductionProtocolSpec`, `ComparisonRegimeSpec`, and `ContinuationSpec`
- `Deficiency`
- `AvailabilityAnalyzer`
- `AvailabilityReport`
- `AvailabilityStatus`
- `render_markdown_report`
- `render_json_report`

Research and experimental APIs may change faster: residual transition helpers,
finite DTMC helpers, statistical verifier helpers, external model-checking
adapters, repair-cover solvers, and experiment utilities. See
[API stability](docs/api-stability.md).

## Strict mode

Normal mode accepts a small number of v0.1 compatibility shortcuts, such as
legacy `metadata["reconstructs_report_path"]`. Strict mode requires
first-class typed specs where applicable and is recommended for reproducible
claim packages:

```bash
uv run python -m cgt_availability diagnose fixtures/conformance/strict_protocol_claim_package.json --pipeline standard --format json --strict
```

## Residual and continuation helpers

Continuation-sensitive diagnostics inspect declared residual constraints,
follow-up tests, refinements, repairs, and finite residual transition systems.
Residual simulation helpers are finite bounded diagnostics, not full
coalgebraic or bisimulation semantics. They are CGT-style continuation readouts
for declared finite structures, not full model checking.

## Level 5 experiment snapshot

The optional Level 5 Ollama Gemma experiment is local-only and isolated under
`experiments/`. It is not a benchmark, not a validation of CGT as a whole, and
not a truth test. Raw prompts and model responses remain ignored; public files
contain aggregate metrics, hashes, and diagnostic summaries only. Ollama and
Gemma models are also not dependencies, and availability conclusions still come
from the deterministic analyzer.

The current v4 public summary is partial live extraction evidence: 80 live
records out of a configured 640-record matrix. The deterministic gold check over
32 synthetic scenarios reports report-only collapse `1.0`, closed-profile
separation `0.642857`, and CGT diagnostic separation `1.0`. The live extraction
subset parsed all responses but recovered shallow packages: average deficiency
F1 `0.47038`, status agreement `40/80`, and diagnostic-signature agreement
`5/80`. See the [experiment documentation](docs/experiments.md) and
[v4 report](experiments/level5_ollama_gemma4/results/v4/report.md).

The experiment can also run `--gold-only` to verify deterministic
theory-separation metrics without Ollama or raw outputs.

```python
from cgt_availability.adapters import PRISM_COMMAND_PROFILE

arguments = PRISM_COMMAND_PROFILE.build_arguments("model.pm", "properties.pctl")
print(arguments)
```

Run the license metadata guard before release checks:

```bash
uv run python tools/license_audit.py --allow-missing
```

## Documentation paths

- [Architecture](docs/architecture.md): module boundaries and analyzer flow
- [API stability](docs/api-stability.md): stable v0.1.0 surface and experimental helpers
- [CGT mapping](docs/cgt_mapping.md): paper vocabulary to Python dataclasses
- [Theory audit](docs/theory_audit.md): implemented, finite approximation, adapter boundary, not implemented, and out-of-scope items
- [Schema](docs/schema.md): JSON Schema artifacts and conformance fixtures
- [Pipeline levels](docs/pipelines.md): staged adoption from minimal to research pipelines
- [Experiments](docs/experiments.md): optional Level 5 local experiment policy and Ollama Gemma harness
- [Limitations](docs/limitations.md): exact limits of the finite implementation
- [License policy](docs/licenses.md): optional dependency and external binary policy
- [Release notes](RELEASE_NOTES.md): v0.1.0 release text for GitHub and Zenodo-style publication

## License

Apache License 2.0. See [LICENSE](LICENSE). This repository intentionally uses
`LICENSE` only and does not include a `NOTICE` file.

## Citation

Takahashi, K. (2026). *Constraint Generative Theory: Typed Constraint Effects
and Scientific Availability*. Zenodo. https://doi.org/10.5281/zenodo.20262492
