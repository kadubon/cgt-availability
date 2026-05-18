"""Shared diagnostic metadata helpers."""

from __future__ import annotations

from cgt_availability.core.package import ClaimPackage


def metadata_bool(pkg: ClaimPackage, key: str) -> bool:
    return bool(pkg.metadata.get(key, False))


def requested_diagnostics(pkg: ClaimPackage) -> tuple[str, ...]:
    raw = pkg.metadata.get("diagnostics_requested", ())
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, list | tuple):
        return tuple(str(item) for item in raw)
    return ()


def diagnostic_requires_dimension(pkg: ClaimPackage, dimension_name: str) -> bool:
    diagnostics = set(requested_diagnostics(pkg))
    if dimension_name in diagnostics:
        return True
    if dimension_name == "marker" and metadata_bool(pkg, "marker_sensitive"):
        return True
    if dimension_name == "continuation" and metadata_bool(pkg, "continuation_sensitive"):
        return True
    if dimension_name == "history" and metadata_bool(pkg, "history_sensitive"):
        return True
    return False


def report_omits_dimension(pkg: ClaimPackage, dimension_name: str) -> bool:
    if pkg.projection is None:
        return False
    omitted = pkg.projection.metadata.get("omits_dimensions", ())
    if isinstance(omitted, str):
        return omitted == dimension_name
    if isinstance(omitted, list | tuple):
        return dimension_name in {str(item) for item in omitted}
    return False
