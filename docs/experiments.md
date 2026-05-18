# Experiments

Experiments live outside the core package. They may import `cgt_availability`,
but `src/cgt_availability` must not import experiment code. This keeps the
library portable and keeps optional research dependencies out of Level 0 and
Level 1 use.

## Level 5 Ollama Gemma Experiment

The current Level 5 experiment is
[`experiments/level5_ollama_gemma4`](../experiments/level5_ollama_gemma4).
It uses a local Ollama chat endpoint with `model="gemma4:e4b"`,
`think=false`, `stream=false`, and `format="json"`.
The v3 experiment configuration uses three extraction arms: `minimal_text`,
`report_only`, and `schema_guided_dossier`. The v4 configuration is the current
finite theory-effect design: 32 counterfactual scenarios, 4 arms, 5 seeds, and
640 configured live records. The added v4 arm, `schema_guided_component_slots`,
uses Ollama's JSON Schema `format` payload mode to require component declaration
slots and short evidence strings while keeping `think=false`.

The experiment's scientific question is narrow:

- Can a report-only baseline distinguish finite synthetic cases with the same
  report or verifier verdict?
- Can the deterministic analyzer distinguish those cases through marker,
  continuation, history, dependency-closure, and strict reproduction
  declarations?
- How stable is LLM-assisted `ClaimPackage` extraction against the synthetic
  gold profiles?
- Does schema-guided extraction improve declaration coverage without leaking
  expected deficiency codes, expected status labels, or gold diagnostic hashes
  into the prompt?

The experiment does not evaluate claim truth, general model intelligence,
general scientific quality, or science/non-science demarcation.

## Evaluation Layers

The Level 5 experiment separates three signatures:

- `report_only_signature`: report and verifier-verdict fields available to a
  report-only baseline.
- `closed_profile_signature`: analyzer status and dependency-closed deficiency
  codes.
- `cgt_diagnostic_signature`: closed profile plus marker, history,
  direct-selector, strict-protocol, and continuation readouts.

This is needed because the paper explicitly allows packages with the same
normalized report, verifier verdict, and dependency-closed deficiency profile to
leave different residual continuation spaces. The gold evaluation checks that
the implementation separates those cases without requiring a live LLM run.

## Data Policy

Published artifacts:

- deterministic synthetic scenario catalog
- experiment configuration
- aggregate metrics
- component-coverage table
- report-separation matrix
- hash manifest
- redacted summary report

Ignored local artifacts:

- raw prompts
- raw model responses
- token traces
- local timing logs with machine identifiers
- `raw/`
- `runs/`
- `*.raw.jsonl`

Raw outputs are excluded because local model/runtime behavior may be
nondeterministic and raw logs can accidentally expose local context. Public
reproducibility means rerunning the generator and harness locally, then
comparing aggregate metrics and hashes within declared tolerances.

## Dependency Boundary

The experiment extra may use table, plotting, validation, or statistical helper
libraries. These libraries are not bundled. Ollama, Gemma model weights, PRISM,
Storm, and `stormpy` are not Python dependencies. Users install and license
external tools and model content separately.

The experiment has two summarization backends:

- `stdlib`: dependency-free public artifact writing for CI and portability.
- `external`: practical experiment analysis with `pandas`, `scipy`,
  `matplotlib`, and `jsonschema`.

The external backend uses `pandas` for grouped tables, `scipy` for finite
binomial confidence intervals, `matplotlib` for an aggregate separation plot,
and `jsonschema` to validate the public experiment contracts. It is still an
experiment-layer dependency only; `src/cgt_availability` does not import these
libraries.

Run a dry request-construction check:

```bash
uv run python experiments/level5_ollama_gemma4/run_ollama_experiment.py --max-cases 1
```

Run the deterministic gold evaluation without Ollama:

```bash
uv run python experiments/level5_ollama_gemma4/summarize_results.py --gold-only
```

Run the practical external-library backend:

```bash
uv sync --extra experiments
uv run python experiments/level5_ollama_gemma4/summarize_results.py \
  --gold-only \
  --analysis-backend external \
  --scenarios experiments/level5_ollama_gemma4/scenario_catalog_v2.json \
  --config experiments/level5_ollama_gemma4/config_v3.json \
  --output-dir experiments/level5_ollama_gemma4/results/v3
```

The external backend writes `diagnostic_signatures.json`,
`component_coverage.csv`, `separation_matrix.csv`, `metrics_summary.json`, and
`separation_rates.png` in addition to the standard public artifacts. v4 also
writes `dimension_effects.csv` and `hypothesis_tests.json`. These files contain
aggregate metrics and public diagnostic signatures only; they do not contain
raw prompts or raw model responses.

Run the v4 deterministic theory-effect evaluation:

```bash
uv sync --extra experiments
uv run python experiments/level5_ollama_gemma4/summarize_results.py \
  --gold-only \
  --analysis-backend external \
  --scenarios experiments/level5_ollama_gemma4/scenario_catalog_v4.json \
  --config experiments/level5_ollama_gemma4/config_v4.json \
  --output-dir experiments/level5_ollama_gemma4/results/v4
```

The standard v4 live matrix is intentionally explicit: 32 scenarios, 4 arms,
and 5 seeds. Summaries include `configured_full_live_run_count`,
`observed_live_combination_count`, `partial_live_run`, and missing
scenario/arm/seed cells so incomplete local runs are not mistaken for complete
evidence.

The current public v4 live summary was generated from
`raw/v4_full.raw.jsonl` but remains partial: 80 records were summarized, covering
4 scenarios, 4 arms, and 5 seeds out of the configured 640-record matrix. The
gold deterministic theory check still covers all 32 synthetic scenarios and
reports report-only collapse `1.0`, closed-profile separation `0.642857`, and
CGT diagnostic separation `1.0`. The live extraction subset parsed all outputs,
with average deficiency F1 `0.47038`, status agreement `40/80`, and
diagnostic-signature agreement `5/80`. Interpret these live extraction numbers
as local extraction evidence, not as the theory-effect result.

To summarize that v4 raw file without publishing raw prompts or responses:

```bash
uv run python experiments/level5_ollama_gemma4/summarize_results.py \
  --analysis-backend external \
  --raw-input experiments/level5_ollama_gemma4/raw/v4_full.raw.jsonl \
  --scenarios experiments/level5_ollama_gemma4/scenario_catalog_v4.json \
  --config experiments/level5_ollama_gemma4/config_v4.json \
  --output-dir experiments/level5_ollama_gemma4/results/v4
```

Run a local live smoke only when Ollama and `gemma4:e4b` are available:

```bash
uv run python experiments/level5_ollama_gemma4/run_ollama_experiment.py \
  --live \
  --model gemma4:e4b \
  --think false \
  --max-cases 1 \
  --config experiments/level5_ollama_gemma4/config_v3.json \
  --scenarios experiments/level5_ollama_gemma4/scenario_catalog_v2.json
```

The 2026-05-18 live run is preserved as a negative extraction baseline under
`results/baselines/2026-05-18-gemma4-e4b-think-false`. It should remain in the
public record: the model produced syntactically valid packages, but generally
failed to extract the richer declarations required for CGT diagnostic
separation. The v3 artifacts do not overwrite that result.

The current v3 live summary in `experiments/level5_ollama_gemma4/results`
contains 60 live records: four scenarios, three arms, and five seeds. This is a
subset of the configured full v3 matrix of 360 records. The report therefore
treats arm-level extraction rates as local evidence for the summarized
scenarios, while the 24-scenario theory separation claim remains the
deterministic gold evaluation.
