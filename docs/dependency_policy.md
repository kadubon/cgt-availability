# Dependency Policy

The core runtime must remain dependency-free and portable. Optional libraries may
be used only behind explicit extras and local import boundaries. See
[`docs/licenses.md`](licenses.md) for the SPDX-style release policy and external
binary boundary.

## Current Extras

- `schema`: `jsonschema` for validating JSON Schema artifacts
- `fast`: `msgspec` for optional fast serialization/schema adapters
- `graph`: `networkx` for richer finite graph algorithms
- `modelcheck`: `networkx` for graph-backed finite model-checking adapters
- `stats`: `scipy` for statistical verifier acceleration and distribution functions
- `opt`: `ortools` for larger weighted repair-cover instances
- `adapters`: `pydantic` for optional adapter models
- `test`: `hypothesis` for property tests
- `research`: `networkx` and `scipy` for finite research helpers
- `experiments`: `pandas`, `matplotlib`, `scipy`, and `jsonschema` for local
  experiment summarization, confidence intervals, plotting, and validation

External model-checking tools such as PRISM or Storm are not Python
dependencies of this project. They may be invoked only through explicit
external-process adapters configured by the user. Do not add `prism`, `storm`,
`stormpy`, or wrapper packages for those tools to project dependencies.

External local LLM tools follow the same boundary. Do not add `ollama`, `gemma`,
model-weight packages, or model-checking binaries to project dependencies. The
Level 5 Ollama Gemma harness calls a user-installed local HTTP service with the
standard library and keeps raw outputs under ignored paths.

The Level 5 external analysis backend may import `pandas`, `scipy`,
`matplotlib`, and `jsonschema` only inside experiment functions. It must remain
outside `src/cgt_availability`, and it must fail with an explicit experiment
dependency error if the `experiments` extra is not installed.

## License Rule

Before each dependency upgrade, verify current license metadata from the package
index or upstream repository. Do not add GPL or AGPL runtime dependencies to
core. If a strongly copyleft tool is ever needed, isolate it behind an
external-process adapter and document the boundary explicitly.

Run the metadata guard before release:

```bash
uv run python tools/license_audit.py --allow-missing
```

Current intended licenses are permissive or weak-copyleft for development-only
tooling: `networkx` and `scipy` are BSD-family, `jsonschema` and `pydantic` are
MIT-family, `msgspec` is BSD-3-Clause, `ortools` is Apache-2.0, and
`hypothesis` is MPL-2.0 for tests only. The `experiments` extra adds local
analysis helpers only; it does not distribute model content. Treat this list as
an audit note, not as a substitute for checking package metadata during
upgrades.

External binaries have their own licenses and distribution terms. The adapter
boundary does not grant permission to redistribute those tools; users must
install and license them separately.

## Import Rule

Optional libraries must not be imported at package import time. Import them
inside the function or adapter that needs them, and keep a deterministic
dependency-free fallback where practical.
