# Level 5 Ollama Gemma Experiment Summary

This public report contains aggregate metrics only. Raw prompts, raw model responses, token traces, and local run logs are not published.

## Run Configuration

- Model: `gemma4:e4b`
- Thinking disabled: `True`
- Pipeline: `research`
- Analysis backend: `external`
- Live records summarized: `80`
- Live scenarios summarized: `4`
- Catalog scenario count: `32`
- Configured full live matrix records: `640`
- Partial live run: `True`
- Raw outputs published: `False`

## Gold Deterministic Theory Check

The synthetic gold packages are evaluated without any LLM output. This checks whether the deterministic analyzer reproduces the paper's finite separation claims.

- Report-only collapse rate: `1.0`
- Closed-profile separation rate: `0.6428571428571429`
- Gold CGT diagnostic separation rate: `1.0`
- Gold CGT lift over report-only separation: `1.0`
- Continuation-sensitive same-closed-profile separations: `2`

Dimension-level gold separation accuracy:
- `almost_sure`: `1.000000` (1/1)
- `continuation`: `1.000000` (3/3)
- `degeneracy_control`: `1.000000` (1/1)
- `dependency_closure`: `1.000000` (1/1)
- `history`: `1.000000` (1/1)
- `marker`: `1.000000` (1/1)
- `marker_policy`: `1.000000` (1/1)
- `marker_state`: `1.000000` (1/1)
- `may_must`: `1.000000` (1/1)
- `protocol_strictness`: `1.000000` (1/1)
- `reproduction_protocol`: `1.000000` (1/1)
- `typed_report_path`: `1.000000` (1/1)

Interpretation: the gold finite scenarios preserve the intended CGT cut. Report-only procedures collapse all same-report groups in the catalog, dependency-closed profiles separate only some of them, and the fuller CGT diagnostic signature separates all declared marker, history, protocol, and continuation cases.

## Live LLM Extraction

The local Ollama model is used only to extract candidate `ClaimPackage` JSON. The availability diagnosis is computed by the deterministic analyzer.

- Live scenarios summarized: `4` (`benchmark_claim`, `unobservable_claim`, `vague_ai_claim`, `verifier_failure_incoherence`)
- Parse errors: `0`
- Average deficiency F1: `0.47038`
- LLM-extracted CGT separation rate: `0.0`

Arm-level extraction summaries:
- `minimal_text`: rows `20`, parse `1.000000`, F1 `0.464131`, diagnostic signature agreement `0.000000`
- `report_only`: rows `20`, parse `1.000000`, F1 `0.464131`, diagnostic signature agreement `0.000000`
- `schema_guided_component_slots`: rows `20`, parse `1.000000`, F1 `0.489131`, diagnostic signature agreement `0.250000`
- `schema_guided_dossier`: rows `20`, parse `1.000000`, F1 `0.464131`, diagnostic signature agreement `0.000000`

Finite binomial confidence intervals are included in `summary.json`.
- Parse rate: `1.000000` (80/80, 95% CI `0.954936`-`1.000000`)
- Status agreement rate: `0.500000` (40/80, 95% CI `0.386048`-`0.613952`)
- Diagnostic signature agreement rate: `0.062500` (5/80, 95% CI `0.020603`-`0.139857`)


Coverage note: this live extraction summary is a subset of the configured full matrix. Interpret arm-level extraction rates as local evidence for the summarized scenarios, not as the complete 24-scenario v3 matrix.

Interpretation: this live run produced syntactically valid packages, but the extracted packages usually omitted the richer declarations needed for marker-, history-, protocol-, and continuation-sensitive diagnosis. That is an extraction limitation, not a truth verdict and not a failure of the deterministic gold theory check.

## Diagnostic Meaning

Report-only collapse means scenarios share a report/verdict signature while the gold CGT diagnostic signature differs. Closed-profile separation uses dependency-closed deficiencies only. CGT separation also includes marker, history, protocol, and continuation readouts.

The experiment evaluates finite extraction stability and deterministic availability diagnostics. It does not evaluate claim truth, model intelligence, or general scientific quality.
