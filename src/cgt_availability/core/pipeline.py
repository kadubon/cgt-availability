"""Pipeline presets from minimal diagnostics to research extensions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from cgt_availability.core.dependencies import DiagnosticVocabulary
from cgt_availability.core.serialization import JSONValue
from cgt_availability.rules.base import FunctionRule, Rule
from cgt_availability.rules.coherence import find_coherence_deficiencies
from cgt_availability.rules.continuation import (
    continuation_warnings,
    find_continuation_deficiencies,
)
from cgt_availability.rules.degeneracy import find_degeneracy_deficiencies
from cgt_availability.rules.marker import find_marker_deficiencies
from cgt_availability.rules.report_factorization import find_report_factorization_deficiencies
from cgt_availability.rules.required_components import find_required_component_deficiencies
from cgt_availability.rules.typing import find_type_deficiencies


class PipelineLevel(StrEnum):
    """Named implementation levels for gradual adoption."""

    MINIMAL = "minimal"
    STANDARD = "standard"
    INTEROP = "interop"
    FINITE_THEORY = "finite_theory"
    SCHEMA = "schema"
    GRAPH = "graph"
    COMPLETION = "completion"
    RESEARCH = "research"


@dataclass(frozen=True)
class AvailabilityPipeline:
    """Declarative analyzer configuration."""

    name: str
    level: PipelineLevel
    rules: tuple[Rule, ...]
    vocabulary: DiagnosticVocabulary = field(default_factory=DiagnosticVocabulary.default)
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    @classmethod
    def minimal(
        cls, vocabulary: DiagnosticVocabulary | None = None
    ) -> AvailabilityPipeline:
        """Level 0: required declarations and dependency closure only."""
        return cls(
            name="minimal",
            level=PipelineLevel.MINIMAL,
            rules=(
                FunctionRule("required_components", find_required_component_deficiencies),
            ),
            vocabulary=vocabulary or DiagnosticVocabulary.default(),
            metadata={
                "dependencies": "standard-library-only",
                "scope": "required components and dependency closure",
            },
        )

    @classmethod
    def standard(
        cls, vocabulary: DiagnosticVocabulary | None = None
    ) -> AvailabilityPipeline:
        """Level 1: standard finite deterministic PoC diagnostics."""
        return cls(
            name="standard",
            level=PipelineLevel.STANDARD,
            rules=_standard_rules(),
            vocabulary=vocabulary or DiagnosticVocabulary.default(),
            metadata={
                "dependencies": "standard-library-only",
                "scope": "finite deterministic diagnostics",
            },
        )

    @classmethod
    def schema(cls, vocabulary: DiagnosticVocabulary | None = None) -> AvailabilityPipeline:
        """Backward-compatible alias for the Level 2 interop pipeline."""
        base = cls.interop(vocabulary)
        return cls._with_level(
            base=base,
            name="schema",
            level=PipelineLevel.SCHEMA,
            extra_metadata={"alias_for": "interop"},
        )

    @classmethod
    def interop(cls, vocabulary: DiagnosticVocabulary | None = None) -> AvailabilityPipeline:
        """Level 2: standard diagnostics plus schema/interop metadata."""
        return cls._with_level(
            base=cls.standard(vocabulary),
            name="interop",
            level=PipelineLevel.INTEROP,
            extra_metadata={
                "schema_version": "1.0",
                "interop": "json-schema-fixtures",
                "cli": "python -m cgt_availability diagnose input.json",
            },
        )

    @classmethod
    def graph(cls, vocabulary: DiagnosticVocabulary | None = None) -> AvailabilityPipeline:
        """Backward-compatible alias for the Level 3 finite-theory pipeline."""
        base = cls.finite_theory(vocabulary)
        return cls._with_level(
            base=base,
            name="graph",
            level=PipelineLevel.GRAPH,
            extra_metadata={"alias_for": "finite_theory"},
        )

    @classmethod
    def finite_theory(
        cls, vocabulary: DiagnosticVocabulary | None = None
    ) -> AvailabilityPipeline:
        """Level 3: finite theory witnesses and typed dependency metadata."""
        return cls._with_level(
            base=cls.standard(vocabulary),
            name="finite_theory",
            level=PipelineLevel.FINITE_THEORY,
            extra_metadata={
                "optional_extra": "graph",
                "graph_backend": "core-finite",
                "witnesses": "factorization,direct_selector,marker,residual",
            },
        )

    @classmethod
    def completion(
        cls, vocabulary: DiagnosticVocabulary | None = None
    ) -> AvailabilityPipeline:
        """Level 4: standard diagnostics with completion-solver metadata."""
        return cls._with_level(
            base=cls.standard(vocabulary),
            name="completion",
            level=PipelineLevel.COMPLETION,
            extra_metadata={"optional_extra": "opt", "completion_backend": "fallback"},
        )

    @classmethod
    def research(
        cls, vocabulary: DiagnosticVocabulary | None = None
    ) -> AvailabilityPipeline:
        """Level 5: research-facing residual and plugin extension metadata."""
        return cls._with_level(
            base=cls.standard(vocabulary),
            name="research",
            level=PipelineLevel.RESEARCH,
            extra_metadata={
                "optional_extra": "research",
                "scope": (
                    "finite run modes, fixed-point iteration, finite DTMC reachability, "
                    "binomial verifier readouts, residual systems, plugins"
                ),
                "finite_research_capabilities": (
                    "may,must,almost_sure,least_fixed_point,residual_simulation,"
                    "finite_dtmc_reachability,binomial_verifier"
                ),
                "advanced_optional_extras": "modelcheck,stats",
                "external_experiments": "level5_ollama_gemma4",
            },
        )

    @classmethod
    def _with_level(
        cls,
        *,
        base: AvailabilityPipeline,
        name: str,
        level: PipelineLevel,
        extra_metadata: dict[str, JSONValue],
    ) -> AvailabilityPipeline:
        metadata = dict(base.metadata)
        metadata.update(extra_metadata)
        return cls(
            name=name,
            level=level,
            rules=base.rules,
            vocabulary=base.vocabulary,
            metadata=metadata,
        )


def _standard_rules() -> tuple[Rule, ...]:
    return (
        FunctionRule("required_components", find_required_component_deficiencies),
        FunctionRule("typing.path", find_type_deficiencies),
        FunctionRule("coherence.verifier_failure_protocol", find_coherence_deficiencies),
        FunctionRule("coherence.degeneracy", find_degeneracy_deficiencies),
        FunctionRule("coherence.report_factorization", find_report_factorization_deficiencies),
        FunctionRule("coherence.marker", find_marker_deficiencies),
        FunctionRule(
            "coherence.continuation",
            find_continuation_deficiencies,
            warning_check=continuation_warnings,
        ),
    )
