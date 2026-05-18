# cgt-availability

`cgt-availability` is a diagnostic library for scientific claim packages.
It does not decide whether a claim is true, and it does not decide whether a
claim is science. It checks whether the claim declares the constraints needed
to be handled scientifically: observation, description, normalization,
verification, failure, reproduction, comparison, provenance, marker policy,
history, degeneracy control, and continuation structure.

The core idea is simple: a report is only a projection of a richer effect
profile. Two packages can have the same report or verifier verdict while
differing in what they make observable, reproducible, repairable, or usable for
follow-up scientific work.

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
Ollama and Gemma models are also not dependencies and are not bundled; the Level
5 experiment harness uses a user-installed local Ollama service only.
The experiment can also run `--gold-only` to verify theory-separation metrics
without Ollama or raw outputs. The LLM is only an extraction assistant for
candidate `ClaimPackage` JSON; availability conclusions come from the
deterministic analyzer.

Run the practical experiment-analysis backend with optional libraries:

```bash
uv sync --extra experiments
uv run python experiments/level5_ollama_gemma4/summarize_results.py \
  --gold-only \
  --analysis-backend external \
  --scenarios experiments/level5_ollama_gemma4/scenario_catalog_v2.json \
  --config experiments/level5_ollama_gemma4/config_v3.json \
  --output-dir experiments/level5_ollama_gemma4/results/v3
```

This writes public aggregate artifacts such as `summary.json`, `metrics.csv`,
`diagnostic_signatures.json`, `component_coverage.csv`,
`separation_matrix.csv`, `metrics_summary.json`, `separation_rates.png`, and
`hash_manifest.json`. Raw prompts and raw model responses remain ignored.

## Level 5 experiment snapshot

The Level 5 local experiment uses Ollama `gemma4:e4b` with `think=false`.
The public artifacts contain aggregate metrics and diagnostic signatures only;
raw prompts and raw model responses are not published.

The deterministic v3 gold check covers 24 synthetic scenarios and reproduces the
intended theory cut: report-only diagnosis collapses all same-report groups
(`1.0`), dependency-closed profiles separate some groups (`0.625`), and the
fuller CGT diagnostic signature separates the declared marker, history,
protocol, and continuation cases (`1.0`). This is a deterministic analyzer
check, not an LLM performance result.

The current v3 live Ollama extraction summary covers 60 records: 4 scenarios,
3 extraction arms, and 5 seeds. It is therefore a subset of the configured full
v3 matrix of 360 records. The run parsed all outputs, but still recovered only
shallow package declarations: average deficiency F1 was `0.472464`, status
agreement was `30/60`, and diagnostic-signature agreement was `5/60`. This is
an extraction limitation, not a truth verdict and not a failure of the
deterministic analyzer.

Detailed v3 artifacts and interpretation are in
[the Level 5 v3 experiment report](experiments/level5_ollama_gemma4/results/report.md).
The earlier 14-scenario live result is preserved under
[`results/baselines/2026-05-18-gemma4-e4b-think-false`](experiments/level5_ollama_gemma4/results/baselines/2026-05-18-gemma4-e4b-think-false)
as a negative extraction baseline. The v3 gold-only artifacts remain in
[`experiments/level5_ollama_gemma4/results/v3`](experiments/level5_ollama_gemma4/results/v3).

The v4 design is the current finite theory-effect experiment. It fixes
`gemma4:e4b`, `think=false`, 32 counterfactual scenarios, 4 extraction arms, and
5 seeds, for a configured full live matrix of 640 records. The primary v4 claim
is deterministic: CGT diagnostic signatures separate same-report groups that a
report-only baseline collapses. The LLM extraction run remains secondary. The
v4 public artifacts are written under
[`experiments/level5_ollama_gemma4/results/v4`](experiments/level5_ollama_gemma4/results/v4)
and include `dimension_effects.csv` and `hypothesis_tests.json`.

The current v4 public summary is intentionally marked as partial live evidence:
it summarizes 80 live records, covering 4 scenarios, 4 arms, and 5 seeds out of
the configured 640-record matrix. The deterministic gold check over all 32
synthetic scenarios gives report-only collapse `1.0`, closed-profile separation
`0.642857`, and CGT diagnostic separation `1.0`. The live extraction subset
parsed all responses, but recovered shallow packages: average deficiency F1 was
`0.47038`, status agreement was `40/80`, and diagnostic-signature agreement was
`5/80`. The component-slot arm was the strongest extraction arm in this subset
with diagnostic-signature agreement `0.25`, but this remains extraction evidence
only. The detailed v4 report is
[`experiments/level5_ollama_gemma4/results/v4/report.md`](experiments/level5_ollama_gemma4/results/v4/report.md).

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
- [CGT mapping](docs/cgt_mapping.md): paper vocabulary to Python dataclasses
- [Theory audit](docs/theory_audit.md): implemented, finite approximation, adapter boundary, not implemented, and out-of-scope items
- [Schema](docs/schema.md): JSON Schema artifacts and conformance fixtures
- [Pipeline levels](docs/pipelines.md): staged adoption from minimal to research pipelines
- [Experiments](docs/experiments.md): optional Level 5 local experiment policy and Ollama Gemma harness
- [Limitations](docs/limitations.md): exact limits of the finite implementation
- [License policy](docs/licenses.md): optional dependency and external binary policy

## License

Apache License 2.0. See [LICENSE](LICENSE). This repository intentionally uses
`LICENSE` only and does not include a `NOTICE` file.

## Citation

Takahashi, K. (2026). *Constraint Generative Theory: Typed Constraint Effects
and Scientific Availability*. Zenodo. https://doi.org/10.5281/zenodo.20262492
