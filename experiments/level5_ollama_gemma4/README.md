# Level 5 Ollama Gemma Experiment

This directory contains an optional external experiment for the Level 5
`research` pipeline. It uses a locally installed Ollama model as an extraction
assistant and then evaluates the extracted `ClaimPackage` objects with the
deterministic `cgt-availability` analyzer.

The experiment is not part of the core library. The core package does not
import this directory, and this repository does not bundle Ollama, Gemma model
weights, raw prompts, raw responses, traces, or local timing logs.

## Scientific Question

The experiment tests a narrow claim about this repository's diagnostic
contribution:

- A report-only baseline collapses cases with the same report or verifier
  verdict.
- CGT availability diagnostics can distinguish finite synthetic cases by
  marker policy, continuation space, history, dependency closure, and strict
  reproduction declarations.
- The LLM is used only to extract candidate `ClaimPackage` JSON. The
  availability conclusion comes from the deterministic analyzer.

It does not evaluate claim truth, model intelligence, general scientific
quality, peer review, or social demarcation.

## What Gets Separated

The public evaluation uses three signatures:

- `report_only_signature`: the report/verdict-only baseline.
- `closed_profile_signature`: status plus dependency-closed deficiency codes.
- `cgt_diagnostic_signature`: closed profile plus continuation readout, marker
  state, history/direct-selector state, and strict protocol reconstruction.

This distinction is essential for the continuation cases: two scenarios can
share the same report and the same closed deficiency profile while differing in
the residual tests, refinements, or repairs left available after the report.

The v3 upgrade adds three extraction arms:

- `minimal_text`: short claim text only, comparable to the 2026-05-18 baseline.
- `report_only`: report/verdict-only negative control.
- `schema_guided_dossier`: natural-language declared constraints plus Ollama
  JSON Schema output format.

The v4 design is the current finite theory-effect experiment. It keeps
`gemma4:e4b`, `think=false`, `temperature=0.0`, and `stream=false`, then uses
32 counterfactual scenarios, 4 arms, and 5 seeds. The fourth arm is
`schema_guided_component_slots`, which requires component declaration slots and
short evidence strings in addition to the candidate `ClaimPackage`.

The earlier 2026-05-18 live result is intentionally preserved under
`results/baselines/2026-05-18-gemma4-e4b-think-false`. It is a negative
extraction baseline: parsing succeeded, but rich CGT declaration extraction was
weak.

## Run Locally

Prepare deterministic synthetic scenarios:

```bash
uv run python experiments/level5_ollama_gemma4/prepare_scenarios.py
```

Dry-run request construction without calling Ollama:

```bash
uv run python experiments/level5_ollama_gemma4/run_ollama_experiment.py --max-cases 1
```

Run one local live scenario if Ollama and `gemma4:e4b` are installed:

```bash
uv run python experiments/level5_ollama_gemma4/run_ollama_experiment.py --live --model gemma4:e4b --think false --max-cases 1
```

Summarize ignored raw outputs into public aggregate artifacts:

```bash
uv run python experiments/level5_ollama_gemma4/summarize_results.py
```

Run the deterministic gold evaluation without Ollama or raw files:

```bash
uv run python experiments/level5_ollama_gemma4/summarize_results.py --gold-only
```

Run the practical external-library analysis backend:

```bash
uv sync --extra experiments
uv run python experiments/level5_ollama_gemma4/summarize_results.py \
  --gold-only \
  --analysis-backend external \
  --scenarios experiments/level5_ollama_gemma4/scenario_catalog_v2.json \
  --config experiments/level5_ollama_gemma4/config_v3.json \
  --output-dir experiments/level5_ollama_gemma4/results/v3
```

The external backend uses `pandas` for metrics tables, `scipy` for finite
binomial confidence intervals, `matplotlib` for a public aggregate plot, and
`jsonschema` for artifact validation. These packages are installed only through
the `experiments` extra and are not bundled by this repository.

Run the v4 deterministic finite theory-effect check:

```bash
uv sync --extra experiments
uv run python experiments/level5_ollama_gemma4/summarize_results.py \
  --gold-only \
  --analysis-backend external \
  --scenarios experiments/level5_ollama_gemma4/scenario_catalog_v4.json \
  --config experiments/level5_ollama_gemma4/config_v4.json \
  --output-dir experiments/level5_ollama_gemma4/results/v4
```

Run the full v4 live matrix only when the local Ollama setup is available and
the expected 640 requests are acceptable:

```bash
uv run python experiments/level5_ollama_gemma4/run_ollama_experiment.py \
  --live \
  --model gemma4:e4b \
  --think false \
  --config experiments/level5_ollama_gemma4/config_v4.json \
  --scenarios experiments/level5_ollama_gemma4/scenario_catalog_v4.json \
  --raw-output experiments/level5_ollama_gemma4/raw/v4_full.raw.jsonl
```

The v4 summary reports `partial_live_run` and every missing scenario/arm/seed
cell if the raw file does not cover the configured full matrix.

Dry-run the v3 request matrix without calling Ollama:

```bash
uv run python experiments/level5_ollama_gemma4/run_ollama_experiment.py \
  --config experiments/level5_ollama_gemma4/config_v3.json \
  --scenarios experiments/level5_ollama_gemma4/scenario_catalog_v2.json \
  --max-cases 1
```

Verify a local summary against a baseline summary:

```bash
uv run python experiments/level5_ollama_gemma4/verify_reproduction.py \
  --actual experiments/level5_ollama_gemma4/results/summary.json \
  --expected experiments/level5_ollama_gemma4/results/summary.json
```

## Configuration

`config.json` fixes the baseline configuration. `config_v3.json` fixes the
upgraded matrix:

- `model="gemma4:e4b"`
- `think=false`
- `stream=false`
- `format="json"`
- fixed seed list
- fixed prompt version
- analyzer pipeline `research`
- extraction arms for v3

The harness uses the standard library HTTP client against
`http://localhost:11434/api/chat`. It does not depend on the Ollama Python
package.

## Public And Non-Public Artifacts

Public:

- `scenario_catalog.json`
- `scenario_catalog_v2.json`
- `scenario_catalog_v4.json`
- `config.json`
- `config_v3.json`
- `config_v4.json`
- `results/summary.json`
- `results/metrics.csv`
- `results/diagnostic_signatures.json`
- `results/component_coverage.csv` in v3 outputs
- `results/separation_matrix.csv` in v3 outputs
- `results/dimension_effects.csv` in v4 outputs
- `results/hypothesis_tests.json` in v4 outputs
- `results/metrics_summary.json` when `--analysis-backend external` is used
- `results/separation_rates.png` when `--analysis-backend external` is used
- `results/report.md`
- `results/hash_manifest.json`
- `results/baselines/2026-05-18-gemma4-e4b-think-false/`

Non-public and ignored:

- `raw/`
- `runs/`
- `*.raw.jsonl`
- raw prompts
- raw model responses
- token traces
- local timing logs with machine identifiers

The public result files include diagnostic signature hashes, aggregate metrics,
schema-validated summaries, and optional aggregate plots. They do not include
raw model response text.

## Current v4 Public Summary

The current v4 public artifacts in `results/v4` were summarized from
`raw/v4_full.raw.jsonl`, but they are not a completed 640-record matrix. They
contain 80 live records: 4 scenarios, 4 extraction arms, and 5 seeds. The
summary therefore sets `partial_live_run=true` and reports the missing
scenario/arm/seed cells.

The deterministic gold theory check covers all 32 synthetic scenarios:

- report-only collapse rate: `1.0`
- closed-profile separation rate: `0.642857`
- CGT diagnostic separation rate: `1.0`
- CGT lift over report-only separation: `1.0`

The live extraction subset parsed all 80 responses but usually missed the richer
declarations needed for CGT-sensitive diagnosis: average deficiency F1 was
`0.47038`, status agreement was `40/80`, and diagnostic-signature agreement was
`5/80`. The `schema_guided_component_slots` arm had the highest
diagnostic-signature agreement in this subset (`0.25`). These numbers evaluate
local extraction behavior, not claim truth and not the deterministic theory
effect.

## License Boundary

Ollama and Gemma are user-installed external components. This repository does
not redistribute the Ollama binary or model weights. Users must check Ollama's
license and Gemma terms for their deployment and publication context before
running or publishing derived experiment results.
