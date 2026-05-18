# Theory Audit

This audit maps the paper's theory to the current implementation. It is not a
runtime judgment and does not classify claims as true, false, science, or
non-science. The machine-readable contract is
[`fixtures/theory_alignment.json`](../fixtures/theory_alignment.json); tests
compare that fixture with `default_theory_alignment_report()`.

## Status Legend

- `implemented`: executable finite behavior is implemented and covered by tests.
- `poc_approximation`: implemented as a finite approximation of a broader
  theoretical definition. The code exposes real behavior, but not the full
  mathematical generality of the paper.
- `adapter_boundary`: represented as an explicit integration boundary to an
  optional library or user-installed external binary.
- `not_implemented`: documented as part of the theory or roadmap, but not
  claimed by the code.
- `out_of_scope`: intentionally excluded from this library.

The TeX anchors below refer to the local TeX source used for this audit. If the
paper source changes, regenerate the machine-readable fixture and recheck the
anchors.

## Alignment Table

| Paper concept | Paper anchor | Implementation symbol | Status | Exact limitation |
| --- | --- | --- | --- | --- |
| partial scientific availability package | TeX:182 | `ClaimPackage`, spec dataclasses | implemented | finite serializable package schema |
| continuation-extended package | TeX:205 | `ContinuationSpec`, residual helpers | poc_approximation | finite declared residual structures only |
| complete package | TeX:213 | `AvailabilityProfile.is_complete` | implemented | completeness means declared required finite components |
| report path | TeX:221 | `ReportPathSpec`, `TypedMapSpec` | poc_approximation | declared maps, not semantic functions |
| well-typed package | TeX:242 | report-path and consumer domain checks | poc_approximation | string-label types, not mathematical domains |
| coherence components | TeX:265 | rule pack | poc_approximation | finite rule checks, no theorem proving |
| coherent package | TeX:284 | `AvailabilityProfile.is_coherent` | poc_approximation | relative to implemented finite rules |
| reproducibly available package | TeX:288 | `ReproductionProtocolSpec.reconstructs` | poc_approximation | strict finite report-path replay declaration |
| availability is not verifier success | TeX:292 | separate profile and verifier readouts | implemented | verifier readout is not availability by itself |
| truth is not the diagnostic target | TeX:296 | README/docs/adapters non-goal | out_of_scope | truth judgment is intentionally excluded |
| primitive deficiency symbols | TeX:302 | `DeficiencyCode`, `DEFICIENCY_CODE_INFO` | implemented | stable finite registry |
| direct deficiency profile | TeX:324 | `AvailabilityReport.deficiencies` | implemented | finite direct rule output |
| package-relative dependency relation | TeX:328 | `DependencyGraph`, `DependencyEdge`, `DependencyCondition` | implemented | finite deterministic relation |
| dependency-closed deficiency profile | TeX:354 | `DependencyClosure`, `DiagnosticVocabulary` | implemented | finite closure |
| availability preorder | TeX:403 | `availability_preorder` | implemented | ordered by dependency-closed deficiency containment |
| coarse availability labels | TeX:431 | `CoarseAvailabilityClass` | poc_approximation | lossy UI/readability summary |
| compatible non-destructive completion | TeX:459 | `PackagePatch`, `CoherentRepairProblem` | poc_approximation | finite patch search, no arbitrary synthesis |
| report-factorization obstruction | TeX:575 | `FactorizationWitness` | poc_approximation | finite witness pairs only |
| history-sensitive diagnostic | TeX:603 | history metadata and omission checks | poc_approximation | finite declared history dimensions |
| residual constraint space | TeX:627 | `ContinuationSpec`, `ResidualConstraintSpec` | poc_approximation | finite residual declarations |
| residual transition system | TeX:650 | `ResidualTransitionSystem.validate` | poc_approximation | finite graph validation |
| residual simulation | TeX:658 | `bounded_residual_simulation` | poc_approximation | bounded label simulation only |
| continuation-sensitive diagnostic | TeX:666 | continuation specs and simulation helpers | poc_approximation | diagnostic-relative finite readout |
| continuation diagnostic preorder | TeX:700 | `continuation_preorder_result` | poc_approximation | bounded explainable preorder |
| marker-sensitive diagnostic | TeX:746 | `MarkerPolicySpec`, `MarkerStateSpec` | poc_approximation | finite marker state/policy declarations |
| direct-selector degeneracy | TeX:762 | degeneracy rules, `DirectSelectorWitness` | poc_approximation | finite witness and control checks |
| deficiency repair cover | TeX:786 | `solve_repair_cover`, `greedy_repair_cover` | implemented | finite exact/greedy algorithms |
| conflict-constrained repair | TeX:819 | candidate conflict filtering | implemented | finite candidate conflicts |
| continuation-sensitive completion | TeX:839 | `ContinuationRepairProblem` | poc_approximation | finite residual-effect threshold |
| cascaded availability completion | TeX:859 | `solve_cascaded_repair` | poc_approximation | finite ordered prerequisite search |
| deficiency lattice and infinitary dependency operator | TeX:872 | `least_fixed_point` | poc_approximation | finite Kleene iteration over code sets |
| transfinite deficiency iteration | TeX:892 | documented non-claim | not_implemented | no ordinal engine |
| nondeterministic may/must/almost-sure availability | TeX:919 | `evaluate_run_modes`, `almost_sure_available` | poc_approximation | finite run families with explicit probabilities |
| coinductive availability | TeX:936 | roadmap item | not_implemented | no stream-level coinductive semantics |
| finite probabilistic availability model readout | TeX:868 | `FiniteDTMC`, reachability helpers | poc_approximation | finite DTMC reachability, not full temporal logic |
| finite statistical verifier readout | TeX:156 | `BernoulliEvidence`, binomial verifier | poc_approximation | statistical readout, not truth |
| external statistical and model-checking tools | TeX:983 | optional adapters | adapter_boundary | explicit tool boundary, no bundled GPL tools |

## Primary Diagnostic Object

The dependency-closed deficiency profile is the primary diagnostic object. The
preorder compares these profiles. `AvailabilityStatus` and
`CoarseAvailabilityClass` are lossy summaries for readers and UI surfaces.

## Current Non-Implemented / Finite Approximation / Adapter Boundary

The implementation deliberately separates executable finite contracts from
broader theoretical directions.

Finite approximations:

- Report-path typing uses explicit string labels for domains and codomains,
  plus finite consumer-domain checks.
- Report-factorization diagnostics use finite witness pairs and declared
  omitted dimensions.
- Residual transition diagnostics use finite graph validation and bounded label
  simulation.
- May/must/almost-sure availability is evaluated over finite run families with
  explicit probabilities.
- Infinitary deficiency closure is represented by finite Kleene iteration over
  deficiency-code sets.

Adapter boundaries:

- Statistical helpers and SciPy-backed readouts support declared verifier
  readouts, not general statistical inference.
- Model-checking integration is an external-process boundary; full
  temporal-logic model checking is delegated to user-installed tools.
- The Level 5 Ollama Gemma experiment is an external local experiment for
  extraction stability. It is not an analyzer dependency and does not make the
  project an LLM service.

Not implemented:

- transfinite ordinal iteration
- coinductive stream availability
- full temporal-logic model checking inside this package
- general statistical inference
- theorem proving
- model or data redistribution

These limits are part of the public contract. They prevent theory terms such as
"infinitary", "coinductive", or "almost-sure" from becoming empty labels: each
implemented term has a finite executable meaning, and each non-finite direction
is explicitly marked as not implemented or delegated.

## Key Theory Constraints Preserved

- Availability is not verifier success.
- Same report does not imply same availability.
- Same verifier verdict does not imply same scientific usefulness.
- Report-only diagnostics are insufficient when the relevant effect dimension
  does not factor through the report projection.
- Continuation-sensitive capacity is diagnostic-relative; larger residual space
  is not automatically better without a declared comparison or readout.
- May/must/almost-sure availability is evaluated over declared finite runs and
  package predicates, not over truth values.
- Fixed-point iteration is finite Kleene iteration over deficiency codes; it is
  not a transfinite engine.
- Probabilistic model-checking helpers currently evaluate finite DTMC
  reachability only; they do not implement temporal-logic model checking.
- Statistical verifier helpers report declared finite test readouts; they do
  not turn statistical significance into truth or availability by themselves.
- Reproducible availability now requires an explicit report-path reconstruction
  declaration. The legacy `metadata["reconstructs_report_path"]` flag is a
  compatibility path only and is rejected by CLI strict mode.
- External adapters are integration boundaries. Their results may support a
  declared verifier, but they do not become truth or social demarcation
  judgments.
