# Level 5 Ollama Gemma Experiment Summary

This public report contains aggregate metrics only. Raw prompts, raw model responses, token traces, and local run logs are not published.

## Run Configuration

- Model: `gemma4:e4b`
- Thinking disabled: `True`
- Pipeline: `research`
- Analysis backend: `external`
- Live records summarized: `60`
- Live scenarios summarized: `4`
- Catalog scenario count: `24`
- Configured full live matrix records: `360`
- Raw outputs published: `False`

## Gold Deterministic Theory Check

The synthetic gold packages are evaluated without any LLM output. This checks whether the deterministic analyzer reproduces the paper's finite separation claims.

- Report-only collapse rate: `1.0`
- Closed-profile separation rate: `0.625`
- Gold CGT diagnostic separation rate: `1.0`
- Continuation-sensitive same-closed-profile separations: `1`

Interpretation: the gold finite scenarios preserve the intended CGT cut. Report-only procedures collapse all same-report groups in the catalog, dependency-closed profiles separate only some of them, and the fuller CGT diagnostic signature separates all declared marker, history, protocol, and continuation cases.

## Live LLM Extraction

The local Ollama model is used only to extract candidate `ClaimPackage` JSON. The availability diagnosis is computed by the deterministic analyzer.

- Live scenarios summarized: `4` (`benchmark_claim`, `unobservable_claim`, `vague_ai_claim`, `verifier_failure_incoherence`)
- Parse errors: `0`
- Average deficiency F1: `0.472464`
- LLM-extracted CGT separation rate: `0.0`

Arm-level extraction summaries:
- `minimal_text`: rows `20`, parse `1.000000`, F1 `0.464131`, diagnostic signature agreement `0.000000`
- `report_only`: rows `20`, parse `1.000000`, F1 `0.464131`, diagnostic signature agreement `0.000000`
- `schema_guided_dossier`: rows `20`, parse `1.000000`, F1 `0.489131`, diagnostic signature agreement `0.250000`

Finite binomial confidence intervals are included in `summary.json`.
- Parse rate: `1.000000` (60/60, 95% CI `0.940371`-`1.000000`)
- Status agreement rate: `0.500000` (30/60, 95% CI `0.368062`-`0.631938`)
- Diagnostic signature agreement rate: `0.083333` (5/60, 95% CI `0.027613`-`0.183858`)


Coverage note: this live extraction summary is a subset of the configured full matrix. Interpret arm-level extraction rates as local evidence for the summarized scenarios, not as the complete 24-scenario v3 matrix.

Interpretation: this live run produced syntactically valid packages, but the extracted packages usually omitted the richer declarations needed for marker-, history-, protocol-, and continuation-sensitive diagnosis. That is an extraction limitation, not a truth verdict and not a failure of the deterministic gold theory check.

## Diagnostic Meaning

Report-only collapse means scenarios share a report/verdict signature while the gold CGT diagnostic signature differs. Closed-profile separation uses dependency-closed deficiencies only. CGT separation also includes marker, history, protocol, and continuation readouts.

The experiment evaluates finite extraction stability and deterministic availability diagnostics. It does not evaluate claim truth, model intelligence, or general scientific quality.
