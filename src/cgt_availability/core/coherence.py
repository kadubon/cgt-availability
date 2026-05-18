"""Metadata-based coherence primitives for the PoC analyzer."""

from __future__ import annotations

from cgt_availability.core.package import ClaimPackage
from cgt_availability.core.specs import BaseSpec, TypedMapSpec

PATH_COMPONENTS = ("projection", "observation", "description", "normalizer")
REPORT_CONSUMERS = ("expected_report", "verifier", "failure_predicate")
PATH_EDGES = (
    ("projection", "observation"),
    ("observation", "description"),
    ("description", "normalizer"),
)
REPRODUCTION_PATH_COMPONENTS = (
    "projection",
    "observation",
    "description",
    "normalizer",
    "verifier",
)
STRICT_METADATA_KEY = "_cgt_strict"


def spec_domain(spec: BaseSpec | None) -> str | None:
    if spec is None:
        return None
    if isinstance(spec, TypedMapSpec):
        return spec.domain
    value = spec.metadata.get("typed_domain")
    if value is not None:
        return str(value)
    value = spec.metadata.get("domain")
    return None if value is None else str(value)


def spec_codomain(spec: BaseSpec | None) -> str | None:
    if spec is None:
        return None
    if isinstance(spec, TypedMapSpec):
        return spec.codomain
    value = spec.metadata.get("typed_codomain")
    if value is not None:
        return str(value)
    value = spec.metadata.get("codomain")
    return None if value is None else str(value)


def spec_report_domain(pkg: ClaimPackage, component_name: str) -> tuple[str, ...]:
    """Return declared normalized-report domains for report consumers."""
    if pkg.report_path is not None and pkg.report_path.declared:
        if component_name == "verifier" and pkg.report_path.verifier_domain:
            return pkg.report_path.verifier_domain
        if component_name == "failure_predicate" and pkg.report_path.failure_domain:
            return pkg.report_path.failure_domain

    spec = getattr(pkg, component_name)
    if spec is None:
        return ()
    values: list[str] = []
    for key in ("domain", "typed_domain", "report_domain", "input_domain"):
        value = spec.metadata.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list | tuple):
            values.extend(str(item) for item in value)
        else:
            values.append(str(value))
    return tuple(dict.fromkeys(values))


def path_type_mismatches(pkg: ClaimPackage) -> tuple[tuple[str, str, str, str], ...]:
    mismatches: list[tuple[str, str, str, str]] = []
    components = report_path_components(pkg)
    for left_name, right_name in PATH_EDGES:
        left = components[left_name]
        right = components[right_name]
        left_codomain = spec_codomain(left)
        right_domain = spec_domain(right)
        if left_codomain is not None and right_domain is not None and left_codomain != right_domain:
            mismatches.append((left_name, right_name, left_codomain, right_domain))
    report_codomain = spec_codomain(components["normalizer"])
    if report_codomain is not None:
        for component_name in REPORT_CONSUMERS:
            for consumer_domain in spec_report_domain(pkg, component_name):
                if report_codomain != consumer_domain:
                    mismatches.append(
                        ("normalizer", component_name, report_codomain, consumer_domain)
                    )
    return tuple(mismatches)


def has_declared_path_types(pkg: ClaimPackage) -> bool:
    components = report_path_components(pkg)
    for component_name in PATH_COMPONENTS:
        spec = components[component_name]
        if spec is None:
            return False
        if spec_domain(spec) is None or spec_codomain(spec) is None:
            return False
    return True


def report_path_components(pkg: ClaimPackage) -> dict[str, BaseSpec | None]:
    if pkg.report_path is not None and pkg.report_path.declared:
        return {
            "projection": pkg.report_path.projection,
            "observation": pkg.report_path.observation,
            "description": pkg.report_path.description_map,
            "normalizer": pkg.report_path.normalizer,
        }
    return {
        "projection": pkg.projection,
        "observation": pkg.observation,
        "description": pkg.description,
        "normalizer": pkg.normalizer,
    }


def verifier_failure_contradiction(pkg: ClaimPackage) -> bool:
    verifier = pkg.verifier
    failure = pkg.failure_predicate
    if verifier is None or failure is None:
        return False
    if verifier.metadata.get("contradicts_failure_predicate") is True:
        return True
    if not failure.implies_verifier_fail:
        return False
    if "fail" not in {str(item) for item in verifier.verdict_domain}:
        return True
    if failure.metadata.get("failure_value") is True:
        verdict = verifier.metadata.get("verdict")
        return verdict is not None and str(verdict) != "fail"
    verdict_on_failure = verifier.metadata.get("verdict_on_declared_failure")
    return verdict_on_failure is not None and str(verdict_on_failure) != "fail"


def protocol_references_unknown_components(pkg: ClaimPackage) -> tuple[str, ...]:
    protocol = pkg.reproduction_protocol
    if protocol is None:
        return ()
    raw = protocol.reconstructs or protocol.metadata.get("references", ())
    references: tuple[str, ...]
    if isinstance(raw, str):
        references = (raw,)
    elif isinstance(raw, list | tuple):
        references = tuple(str(item) for item in raw)
    else:
        return ()
    known = set(pkg._SPEC_FIELDS) | {"provenance", "metadata"}
    return tuple(sorted(reference for reference in references if reference not in known))


def protocol_missing_reconstructed_components(pkg: ClaimPackage) -> tuple[str, ...]:
    protocol = pkg.reproduction_protocol
    if protocol is None:
        return ()
    if protocol_uses_legacy_reconstructs(pkg) and not strict_mode(pkg):
        return ()
    required = set(REPRODUCTION_PATH_COMPONENTS)
    declared = set(protocol.reconstructs)
    return tuple(sorted(required - declared))


def protocol_reconstructs_report_path(pkg: ClaimPackage) -> bool:
    """Return whether the protocol declares enough data to reconstruct the report path."""
    return not protocol_missing_reconstructed_components(pkg)


def protocol_uses_legacy_reconstructs(pkg: ClaimPackage) -> bool:
    protocol = pkg.reproduction_protocol
    return protocol is not None and protocol.metadata.get("reconstructs_report_path") is True


def strict_mode(pkg: ClaimPackage) -> bool:
    return bool(pkg.metadata.get(STRICT_METADATA_KEY, False))
