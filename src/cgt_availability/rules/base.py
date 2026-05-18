"""Shared rule protocol for finite availability diagnostics."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Protocol

from cgt_availability.core.deficiency import Deficiency
from cgt_availability.core.package import ClaimPackage
from cgt_availability.core.serialization import JSONValue

DeficiencyCheck = Callable[[ClaimPackage], Iterable[Deficiency]]
WarningCheck = Callable[[ClaimPackage], Iterable[str]]


@dataclass(frozen=True)
class RuleResult:
    """Result emitted by one diagnostic rule."""

    deficiencies: tuple[Deficiency, ...] = ()
    warnings: tuple[str, ...] = ()
    metadata: dict[str, JSONValue] = field(default_factory=dict)


class Rule(Protocol):
    """A side-effect-free diagnostic rule."""

    @property
    def name(self) -> str:
        """Stable rule identifier."""

    def evaluate(self, pkg: ClaimPackage) -> RuleResult:
        """Evaluate a package and return deficiencies, warnings, and metadata."""


@dataclass(frozen=True)
class FunctionRule:
    """Adapter for existing deficiency functions."""

    name: str
    check: DeficiencyCheck
    warning_check: WarningCheck | None = None
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def evaluate(self, pkg: ClaimPackage) -> RuleResult:
        warnings = () if self.warning_check is None else tuple(self.warning_check(pkg))
        return RuleResult(
            deficiencies=tuple(self.check(pkg)),
            warnings=warnings,
            metadata=dict(self.metadata),
        )
