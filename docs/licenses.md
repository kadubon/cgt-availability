# License And Dependency Policy

`cgt-availability` is Apache-2.0 licensed and intentionally has no required
runtime dependency outside the Python standard library.

This project does not include a `NOTICE` file. Preserve `LICENSE` only for this
repository; do not add a `NOTICE` file as part of routine release work.

## Runtime Policy

- Core runtime dependencies must remain empty.
- Optional Python dependencies must be installed only through extras and isolated
  behind lazy imports.
- Optional dependencies are not bundled in this repository.
- GPL/AGPL Python runtime dependencies are not allowed in core, default
  installation, or documented default extras.
- LGPL/MPL dependencies are not automatically denied, but any new runtime use
  needs review before release.
- External binaries with GPL/AGPL licenses may be supported only through
  user-installed external-process adapters. They must not be vendored, bundled,
  or declared as Python dependencies.

## Current Optional Dependencies

| Extra | Package | License policy note |
| --- | --- | --- |
| `schema` | `jsonschema` | MIT according to package metadata sources; use the base package and do not add GPL-related format extras |
| `fast` | `msgspec` | BSD-3-Clause according to PyPI metadata |
| `graph` / `modelcheck` | `networkx` | BSD-3-Clause according to PyPI and project metadata |
| `stats` | `scipy` | BSD License according to PyPI metadata |
| `opt` | `ortools` | Apache-2.0 according to PyPI metadata |
| `adapters` | `pydantic` | MIT according to upstream license metadata |
| `test` | `hypothesis` | MPL-2.0, test-only |
| `experiments` | `pandas`, `matplotlib`, `scipy`, `jsonschema` | local experiment-only tables, intervals, plots, and schema validation; not bundled and not imported by core |

References used for the current policy:

- [SciPy PyPI](https://pypi.org/project/scipy/)
- [pandas PyPI](https://pypi.org/pypi/pandas)
- [Matplotlib license documentation](https://matplotlib.org/3.2.1/devel/license.html)
- [NetworkX PyPI](https://pypi.org/project/networkx/)
- [OR-Tools PyPI](https://pypi.org/pypi/ortools/)
- [msgspec PyPI](https://pypi.org/project/msgspec/)
- [jsonschema package metadata](https://packages.ecosyste.ms/registries/pypi.org/packages/jsonschema)
- [Pydantic LICENSE](https://github.com/pydantic/pydantic/blob/main/LICENSE)
- [Hypothesis PyPI](https://pypi.org/pypi/hypothesis)

## External Model Checkers

PRISM and Storm are supported only as external-process adapter targets.
They are not vendored, bundled, or listed as Python dependencies.

- [PRISM](https://www.prismmodelchecker.org/download.php) is distributed under GPL v2 according to its download/license page.
- [Storm](https://github.com/moves-rwth/storm) is GPL-3.0 licensed according to its repository metadata.
- `stormpy` is also GPL-3.0 licensed and must not be added as a Python dependency.

Users who install these tools are responsible for checking the relevant tool
licenses for their deployment context. The adapter boundary records command
construction and execution results; it does not redistribute the tools.

## External Local LLM Experiments

The Level 5 Ollama Gemma experiment is an optional local experiment, not a core
runtime feature.

- Ollama is not bundled or declared as a Python dependency.
- Gemma model weights are not bundled, cached, mirrored, or redistributed.
- Experiment analysis libraries are installed only through the `experiments`
  extra and are not vendored into this repository.
- Raw prompts, raw model outputs, traces, and local run logs are ignored and not
  published.
- Users must review the Ollama license and Gemma terms before running the
  experiment or publishing derived results.
- The experiment uses Ollama's HTTP API with `think=false`; it does not use the
  Ollama Python package.

References:

- [Ollama LICENSE](https://github.com/ollama/ollama/blob/main/LICENSE)
- [Ollama thinking parameter](https://ollama.com/blog/thinking)
- [Gemma Terms of Use](https://ai.google.dev/gemma/terms)

## Upgrade Checklist

Before adding or upgrading any dependency:

1. Check the dependency's PyPI metadata and upstream repository license.
2. Check transitive dependencies for GPL/AGPL runtime exposure.
3. Keep the package in an optional extra unless it is essential to Level 0/1.
4. Run:

   ```bash
   uv run python tools/license_audit.py --allow-missing
   ```

5. Update this document if any package, license, or boundary changes.
6. Do not add a `NOTICE` file.

## Automated Audit

`tools/license_audit.py` is a standard-library script that inspects installed
distribution metadata through `importlib.metadata`, emits JSON, and exits
non-zero if GPL/AGPL Python dependencies are detected.

It is intentionally conservative and metadata-based. It is a release guard, not
a legal opinion.
