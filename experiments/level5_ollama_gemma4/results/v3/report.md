# Level 5 Ollama Gemma Experiment Summary

This public report contains aggregate metrics only. Raw prompts, raw model responses, token traces, and local run logs are not published.

## Run Configuration

- Model: `gemma4:e4b`
- Thinking disabled: `True`
- Pipeline: `research`
- Analysis backend: `external`
- Live records summarized: `0`
- Scenario count: `24`
- Raw outputs published: `False`

## Gold Deterministic Theory Check

The synthetic gold packages are evaluated without any LLM output. This checks whether the deterministic analyzer reproduces the paper's finite separation claims.

- Report-only collapse rate: `1.0`
- Closed-profile separation rate: `0.625`
- Gold CGT diagnostic separation rate: `1.0`
- Continuation-sensitive same-closed-profile separations: `1`

Interpretation: the gold finite scenarios preserve the intended CGT cut. Report-only procedures collapse all same-report groups in the catalog, dependency-closed profiles separate only some of them, and the fuller CGT diagnostic signature separates all declared marker, history, protocol, and continuation cases.

## Live LLM Extraction

No live LLM outputs are summarized in this artifact. The metric rows come from deterministic gold packages only, so perfect parse, status, or diagnostic-signature agreement here is a gold self-check, not an LLM extraction result. Run `run_ollama_experiment.py --live` locally and summarize the ignored raw JSONL to evaluate extraction.

## Diagnostic Meaning

Report-only collapse means scenarios share a report/verdict signature while the gold CGT diagnostic signature differs. Closed-profile separation uses dependency-closed deficiencies only. CGT separation also includes marker, history, protocol, and continuation readouts.

The experiment evaluates finite extraction stability and deterministic availability diagnostics. It does not evaluate claim truth, model intelligence, or general scientific quality.
