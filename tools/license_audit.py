"""Stdlib license audit for cgt-availability runtime environments."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from importlib import metadata

DEFAULT_DENYLIST = ("GPL", "AGPL")
PERMISSIVE_LICENSE_CLASSIFIERS = (
    "License :: OSI Approved :: Apache Software License",
    "License :: OSI Approved :: BSD License",
    "License :: OSI Approved :: MIT License",
    "License :: OSI Approved :: Python Software Foundation License",
)


@dataclass(frozen=True)
class PackageLicenseRecord:
    """Installed distribution license metadata."""

    name: str
    version: str
    license: str
    classifiers: tuple[str, ...]
    denylisted: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "license": self.license,
            "classifiers": list(self.classifiers),
            "denylisted": self.denylisted,
        }


def is_denylisted_license(
    license_text: str,
    *,
    denylist: tuple[str, ...] = DEFAULT_DENYLIST,
) -> bool:
    """Return whether license metadata indicates GPL/AGPL strong copyleft.

    LGPL and MPL are not treated as GPL/AGPL denials by this repository policy.
    """
    text = license_text.upper()
    if not text:
        return False
    if "LGPL" in text or "LESSER GENERAL PUBLIC LICENSE" in text:
        text = text.replace("LGPL", "")
        text = text.replace("LESSER GENERAL PUBLIC LICENSE", "")
    deny = {item.upper() for item in denylist}
    if "AGPL" in deny and (
        "AGPL" in text or "AFFERO GENERAL PUBLIC LICENSE" in text
    ):
        return True
    if "GPL" in deny:
        if "GNU GENERAL PUBLIC LICENSE" in text:
            return True
        if re.search(r"(?<![A-Z])GPL(?:[-_ ]?(?:V|VERSION)?\d|\b)", text):
            return True
    return False


def installed_license_records(
    package_names: tuple[str, ...] = (),
    *,
    denylist: tuple[str, ...] = DEFAULT_DENYLIST,
) -> tuple[PackageLicenseRecord, ...]:
    """Return sorted license records for installed distributions."""
    requested = {normalize_name(name) for name in package_names}
    records: list[PackageLicenseRecord] = []
    for distribution in metadata.distributions():
        name = distribution.metadata.get("Name", distribution.name)
        normalized = normalize_name(name)
        if requested and normalized not in requested:
            continue
        classifiers = tuple(distribution.metadata.get_all("Classifier") or ())
        license_value = distribution.metadata.get("License", "")
        license_expression = distribution.metadata.get("License-Expression", "")
        license_source = license_evidence_for_denylist(
            license_value=license_value,
            license_expression=license_expression,
            classifiers=classifiers,
        )
        records.append(
            PackageLicenseRecord(
                name=name,
                version=distribution.version,
                license=license_value,
                classifiers=classifiers,
                denylisted=is_denylisted_license(license_source, denylist=denylist),
            )
        )
    return tuple(sorted(records, key=lambda item: normalize_name(item.name)))


def license_evidence_for_denylist(
    *,
    license_value: str,
    license_expression: str,
    classifiers: tuple[str, ...],
) -> str:
    """Return concise license evidence for GPL/AGPL denial checks.

    Some scientific packages place bundled third-party license notices in the
    metadata `License` field. When a package declares a standard permissive OSI
    classifier and has no SPDX expression, use the classifier as the top-level
    denylist signal to avoid treating copied notice text as the project license.
    """
    if license_expression:
        return " ".join((license_expression, *classifiers))
    if has_permissive_license_classifier(classifiers) and len(license_value) > 1000:
        return " ".join(classifiers)
    return " ".join((license_value, *classifiers))


def has_permissive_license_classifier(classifiers: tuple[str, ...]) -> bool:
    return any(item in PERMISSIVE_LICENSE_CLASSIFIERS for item in classifiers)


def normalize_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def build_audit_report(
    package_names: tuple[str, ...] = (),
    *,
    allow_missing: bool = False,
    denylist: tuple[str, ...] = DEFAULT_DENYLIST,
) -> dict[str, object]:
    records = installed_license_records(package_names, denylist=denylist)
    found = {normalize_name(record.name) for record in records}
    requested = {normalize_name(name) for name in package_names}
    missing = tuple(sorted(requested - found))
    denylisted = tuple(record.name for record in records if record.denylisted)
    ok = not denylisted and (allow_missing or not missing)
    return {
        "ok": ok,
        "denylist": list(denylist),
        "missing": list(missing),
        "denylisted": list(denylisted),
        "packages": [record.to_dict() for record in records],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", nargs="*", default=())
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--deny", nargs="*", default=DEFAULT_DENYLIST)
    args = parser.parse_args(argv)
    report = build_audit_report(
        tuple(args.packages),
        allow_missing=bool(args.allow_missing),
        denylist=tuple(str(item) for item in args.deny),
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
