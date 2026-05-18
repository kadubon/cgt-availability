# Level 5 Ollama Gemma Experiment Summary

This public report contains aggregate metrics only. Raw prompts, raw model responses, token traces, and local run logs are not published.

## Run Configuration

- Model: `gemma4:e4b`
- Thinking disabled: `True`
- Pipeline: `research`
- Analysis backend: `external`
- Live records summarized: `70`
- Scenario count: `14`
- Raw outputs published: `False`

## Gold Deterministic Theory Check

The synthetic gold packages are evaluated without any LLM output. This checks whether the deterministic analyzer reproduces the paper's finite separation claims.

- Report-only collapse rate: `1.0`
- Closed-profile separation rate: `0.75`
- Gold CGT diagnostic separation rate: `1.0`
- Continuation-sensitive same-closed-profile separations: `1`

Interpretation: the gold finite scenarios preserve the intended CGT cut. Report-only procedures collapse all same-report groups in the catalog, dependency-closed profiles separate only some of them, and the fuller CGT diagnostic signature separates all declared marker, history, protocol, and continuation cases.

## Live LLM Extraction

The local Ollama model is used only to extract candidate `ClaimPackage` JSON. The availability diagnosis is computed by the deterministic analyzer.

- Parse errors: `0`
- Average deficiency F1: `0.220704`
- LLM-extracted CGT separation rate: `0.0`

Finite binomial confidence intervals are included in `summary.json`.
- Parse rate: `1.000000` (70/70, 95% CI `0.948666`-`1.000000`)
- Status agreement rate: `0.214286` (15/70, 95% CI `0.125184`-`0.328685`)
- Diagnostic signature agreement rate: `0.000000` (0/70, 95% CI `0.000000`-`0.051334`)

Interpretation: this live run produced syntactically valid packages, but the extracted packages usually omitted the richer declarations needed for marker-, history-, protocol-, and continuation-sensitive diagnosis. That is an extraction limitation, not a truth verdict and not a failure of the deterministic gold theory check.

## Diagnostic Meaning

Report-only collapse means scenarios share a report/verdict signature while the gold CGT diagnostic signature differs. Closed-profile separation uses dependency-closed deficiencies only. CGT separation also includes marker, history, protocol, and continuation readouts.

The experiment evaluates finite extraction stability and deterministic availability diagnostics. It does not evaluate claim truth, model intelligence, or general scientific quality.
