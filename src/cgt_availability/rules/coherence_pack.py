"""Composable coherence rule packs."""

from __future__ import annotations

from dataclasses import dataclass

from cgt_availability.core.deficiency import Deficiency
from cgt_availability.core.package import ClaimPackage
from cgt_availability.rules.base import FunctionRule, Rule
from cgt_availability.rules.coherence import find_coherence_deficiencies
from cgt_availability.rules.continuation import (
    continuation_warnings,
    find_continuation_deficiencies,
)
from cgt_availability.rules.degeneracy import find_degeneracy_deficiencies
from cgt_availability.rules.marker import find_marker_deficiencies
from cgt_availability.rules.report_factorization import find_report_factorization_deficiencies
from cgt_availability.rules.typing import find_type_deficiencies


@dataclass(frozen=True)
class CoherenceRulePack:
    """Named group of finite coherence-oriented diagnostic rules."""

    path: Rule
    verifier_failure: Rule
    protocol_reproduction: Rule
    degeneracy: Rule
    report_factorization: Rule
    marker: Rule
    continuation: Rule

    @classmethod
    def default(cls) -> CoherenceRulePack:
        """Return the standard finite deterministic coherence rule pack."""
        return cls(
            path=FunctionRule("typing.path", find_type_deficiencies),
            verifier_failure=FunctionRule(
                "coherence.verifier_failure", _verifier_failure_deficiencies
            ),
            protocol_reproduction=FunctionRule(
                "coherence.reproduction_protocol", _protocol_reproduction_deficiencies
            ),
            degeneracy=FunctionRule("coherence.degeneracy", find_degeneracy_deficiencies),
            report_factorization=FunctionRule(
                "coherence.report_factorization", find_report_factorization_deficiencies
            ),
            marker=FunctionRule("coherence.marker", find_marker_deficiencies),
            continuation=FunctionRule(
                "coherence.continuation",
                find_continuation_deficiencies,
                warning_check=continuation_warnings,
            ),
        )

    def as_rules(self) -> tuple[Rule, ...]:
        """Return rules in deterministic execution order."""
        return (
            self.path,
            self.verifier_failure,
            self.protocol_reproduction,
            self.degeneracy,
            self.report_factorization,
            self.marker,
            self.continuation,
        )


def _verifier_failure_deficiencies(pkg: ClaimPackage) -> tuple[Deficiency, ...]:
    return tuple(
        deficiency
        for deficiency in find_coherence_deficiencies(pkg)
        if deficiency.code == "verifier_failure_incoherent"
    )


def _protocol_reproduction_deficiencies(pkg: ClaimPackage) -> tuple[Deficiency, ...]:
    return tuple(
        deficiency
        for deficiency in find_coherence_deficiencies(pkg)
        if deficiency.code == "protocol_incoherent"
    )
