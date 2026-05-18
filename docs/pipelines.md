# Pipeline Levels

`AvailabilityPipeline` makes adoption gradual. Each level keeps the same input
and output shape:

```text
ClaimPackage -> AvailabilityReport
```

## Level Summary

| Level | Pipeline | Input | Runs | Dependencies | Typical use |
| --- | --- | --- | --- | --- | --- |
| 0 | `minimal` | `ClaimPackage` | required components and dependency closure | standard library only | portable baseline and other-language ports |
| 1 | `standard` | `ClaimPackage` | default finite rule registry | standard library only | normal library use and examples |
| 2 | `interop` / `schema` | JSON or `ClaimPackage` | standard diagnostics plus schema/fixture metadata | optional `schema` extra for validation | CLI and cross-language conformance |
| 3 | `finite_theory` / `graph` | `ClaimPackage` plus finite witnesses when needed | structured dependency metadata, factorization witnesses, direct-selector witnesses, marker state, bounded residual simulation | optional graph tooling outside core | richer finite diagnostics |
| 4 | `completion` | repair problems and packages | repair cover, cascaded repair, coherent patch checks | optional `opt` extra for larger weighted cases | completion planning |
| 5 | `research` | finite run families, finite operators, finite models, optional external experiments | may/must/almost-sure checks, finite fixed points, finite DTMC reachability, finite statistical readouts, residual systems, redacted experiment summaries | optional `stats`, `modelcheck`, `research`, or `experiments` extras | executable research-facing fragments and local experiment harnesses |

## Strict Mode

The CLI accepts `--strict`. Strict mode rejects legacy protocol metadata such as
`metadata["reconstructs_report_path"]` when no explicit
`ReproductionProtocolSpec.reconstructs` list is declared.

Library callers can set pipeline metadata `{"strict": true}` to get the same
strict analyzer semantics without changing the public package schema.

## Dependency Rule

Levels 0 and 1 are the reference dependency-free behavior. Higher levels may use
optional extras, but the extras are not bundled and are not imported at package
import time.

External model-checker support is an adapter boundary. PRISM and Storm must be
installed by the user and invoked as external commands.

External LLM-assisted experiments follow the same boundary. The Ollama Gemma
Level 5 harness is local, optional, and isolated under `experiments/`; it does
not change the analyzer into an LLM service.
