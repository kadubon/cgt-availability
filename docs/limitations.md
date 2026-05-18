# Limitations

`cgt-availability` is a finite diagnostic implementation. It intentionally
keeps truth judgment, social demarcation, theorem proving, full statistical
inference, full model checking, and LLM services outside the core.

## Intentional Non-Goals

- It does not decide truth.
- It does not classify claims as science or non-science.
- It does not replace philosophy of science, statistics, model checking, peer
  review, FAIR practice, or reproducibility work.
- It does not infer scientific merit from a verifier pass or a benchmark score.
- It does not use LLM calls or network services in the analyzer.
- Optional LLM-assisted experiments are local extraction studies outside the
  analyzer, not availability decision procedures.

## Implemented As Finite Approximations

- Type checks are declared domain/codomain compatibility checks, not full type
  theory over mathematical domains.
- Verifier/failure coherence uses explicit finite declarations and metadata
  flags.
- Report-factorization diagnostics depend on declared omitted dimensions and
  finite witnesses.
- Direct-selector degeneracy is a diagnostic risk and witness check, not an
  accusation of misconduct.
- Marker-sensitive diagnostics use local marker-policy and marker-state
  declarations.
- Continuation-sensitive diagnostics inspect declared finite residual lists,
  typed residual constraint specs, and bounded residual simulations.
- Repair cover solves finite candidate-selection problems; coherent repair
  checks finite package patches through the analyzer.
- Cascaded repair handles finite ordered prerequisites but does not synthesize
  arbitrary coherent packages.
- Almost-sure availability requires explicit finite run probabilities.
- Fixed-point helpers implement finite Kleene iteration over deficiency-code
  sets.
- Finite DTMC helpers compute reachability probabilities only.
- Statistical verifier helpers cover finite Bernoulli/binomial readouts and
  Wilson intervals.

## Not Implemented

- Transfinite ordinal iteration.
- Coinductive stream-level availability semantics.
- General probabilistic model checking, including PCTL, CTL, LTL, CSL, or full
  PRISM/Storm semantics.
- General statistical inference, causal inference, multiple-testing policy,
  Bayesian updating, benchmark-leakage analysis, or peer-review scoring.
- Network-backed provenance stores.

## Adapter Boundaries

External model-checking adapters call user-provided binaries. PRISM and Storm
are not vendored and are not Python dependencies. Adapter results can support a
declared verifier readout, but they do not make this package a model checker.

The Ollama Gemma Level 5 experiment calls a user-installed local Ollama service
from `experiments/`. It publishes aggregate metrics and hashes only. It does not
publish raw prompts or responses and does not make the package an LLM service.

Optional libraries are installed only through extras and imported lazily. The
core runtime remains standard-library only.
