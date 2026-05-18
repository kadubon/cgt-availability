"""Finite dependency closure for deficiencies."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from cgt_availability.core.deficiency import Deficiency, make_deficiency
from cgt_availability.core.diagnostics import diagnostic_requires_dimension
from cgt_availability.core.package import ClaimPackage
from cgt_availability.core.serialization import JSONValue, ensure_json_object

DEFAULT_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "missing_projection": ("missing_observation",),
    "missing_observation": ("missing_description",),
    "missing_description": ("missing_normalizer",),
    "missing_normalizer": ("missing_verifier", "missing_failure_predicate"),
    "missing_expected_report": ("missing_verifier", "missing_failure_predicate"),
    "missing_history": ("direct_selector_degeneracy_risk",),
    "missing_continuation": ("continuation_sensitive_missing_continuation",),
    "missing_marker_policy": ("marker_sensitive_missing_marker_policy",),
}


@dataclass(frozen=True)
class DependencyCondition:
    """Portable structured activation condition for dependency edges."""

    kind: str
    dimension: str | None = None
    metadata_key: str | None = None
    metadata_value: JSONValue = None
    component: str | None = None
    children: tuple[DependencyCondition, ...] = ()

    @classmethod
    def requires_dimension(cls, dimension: str) -> DependencyCondition:
        return cls(kind="requires_dimension", dimension=dimension)

    @classmethod
    def metadata_equals(cls, key: str, value: JSONValue) -> DependencyCondition:
        return cls(kind="metadata_equals", metadata_key=key, metadata_value=value)

    @classmethod
    def component_missing(cls, component: str) -> DependencyCondition:
        return cls(kind="component_missing", component=component)

    @classmethod
    def component_present(cls, component: str) -> DependencyCondition:
        return cls(kind="component_present", component=component)

    @classmethod
    def component_declared(cls, component: str) -> DependencyCondition:
        return cls(kind="component_declared", component=component)

    @classmethod
    def component_metadata_equals(
        cls, component: str, key: str, value: JSONValue
    ) -> DependencyCondition:
        return cls(
            kind="component_metadata_equals",
            component=component,
            metadata_key=key,
            metadata_value=value,
        )

    @classmethod
    def all_of(cls, *children: DependencyCondition) -> DependencyCondition:
        return cls(kind="all_of", children=tuple(children))

    @classmethod
    def any_of(cls, *children: DependencyCondition) -> DependencyCondition:
        return cls(kind="any_of", children=tuple(children))

    @classmethod
    def not_(cls, child: DependencyCondition) -> DependencyCondition:
        return cls(kind="not", children=(child,))

    def active_for(self, pkg: ClaimPackage | None) -> bool:
        if pkg is None:
            return True
        if self.kind == "requires_dimension":
            return self.dimension is not None and diagnostic_requires_dimension(pkg, self.dimension)
        if self.kind == "metadata_equals":
            return self.metadata_key is not None and pkg.metadata.get(
                self.metadata_key
            ) == self.metadata_value
        if self.kind == "component_missing":
            if self.component is None or not hasattr(pkg, self.component):
                return False
            component = getattr(pkg, self.component)
            return component is None or not bool(getattr(component, "declared", False))
        if self.kind == "component_present":
            return self.component is not None and hasattr(pkg, self.component) and (
                getattr(pkg, self.component) is not None
            )
        if self.kind == "component_declared":
            if self.component is None or not hasattr(pkg, self.component):
                return False
            component = getattr(pkg, self.component)
            return component is not None and bool(getattr(component, "declared", False))
        if self.kind == "component_metadata_equals":
            if (
                self.component is None
                or self.metadata_key is None
                or not hasattr(pkg, self.component)
            ):
                return False
            component = getattr(pkg, self.component)
            metadata = getattr(component, "metadata", {}) if component is not None else {}
            return isinstance(metadata, dict) and metadata.get(
                self.metadata_key
            ) == self.metadata_value
        if self.kind == "all_of":
            return all(child.active_for(pkg) for child in self.children)
        if self.kind == "any_of":
            return any(child.active_for(pkg) for child in self.children)
        if self.kind == "not":
            return bool(self.children) and not self.children[0].active_for(pkg)
        return bool(pkg.metadata.get(self.kind, False))

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class DependencyEdge:
    """A typed dependency edge in a package-relative diagnostic graph."""

    source: str
    target: str
    condition: str | None = None
    structured_condition: DependencyCondition | None = None
    source_component: str | None = None
    target_component: str | None = None
    activation_condition: str | None = None
    rationale: str | None = None

    def active_for(self, pkg: ClaimPackage | None) -> bool:
        if self.structured_condition is not None:
            return self.structured_condition.active_for(pkg)
        condition = self.activation_condition or self.condition
        if condition is None or pkg is None:
            return True
        if condition.endswith("_sensitive"):
            dimension = condition.removesuffix("_sensitive")
            return diagnostic_requires_dimension(pkg, dimension)
        return bool(pkg.metadata.get(condition, False))


@dataclass(frozen=True)
class DependencyGraph:
    """Finite package-relative deficiency dependency graph."""

    edges: tuple[DependencyEdge, ...]

    @classmethod
    def from_mapping(cls, dependencies: Mapping[str, Iterable[str]]) -> DependencyGraph:
        edges = tuple(
            DependencyEdge(
                source=source,
                target=target,
                rationale="Default finite dependency closure edge.",
            )
            for source, targets in dependencies.items()
            for target in targets
        )
        return cls(edges=edges)

    def active_mapping(self, pkg: ClaimPackage | None = None) -> dict[str, tuple[str, ...]]:
        grouped: dict[str, list[str]] = {}
        for edge in self.edges:
            if edge.active_for(pkg):
                grouped.setdefault(edge.source, []).append(edge.target)
        return {source: tuple(targets) for source, targets in grouped.items()}


@dataclass(frozen=True)
class DiagnosticVocabulary:
    """Declared finite diagnostic vocabulary and its dependency graph."""

    name: str
    dependency_graph: DependencyGraph
    version: str = "1.0"
    required_dimensions: tuple[str, ...] = ()

    @classmethod
    def default(cls) -> DiagnosticVocabulary:
        edges = list(DependencyGraph.from_mapping(DEFAULT_DEPENDENCIES).edges)
        edges.append(
            DependencyEdge(
                source="missing_continuation",
                target="report_path_type_error",
                condition="continuation_sensitive",
                structured_condition=DependencyCondition.requires_dimension("continuation"),
                source_component="continuation",
                target_component="report_path",
                activation_condition="continuation_sensitive",
                rationale=(
                    "A continuation-sensitive diagnostic cannot type its report path "
                    "without the continuation component it asks to read."
                ),
            )
        )
        return cls(
            name="finite-deterministic-cgt-availability",
            dependency_graph=DependencyGraph(tuple(edges)),
            version="1.0",
            required_dimensions=("history", "marker", "continuation"),
        )

    def dependency_mapping_for(self, pkg: ClaimPackage | None = None) -> dict[str, tuple[str, ...]]:
        return self.dependency_graph.active_mapping(pkg)


class DependencyClosure:
    """Package-relative finite closure over deficiency codes."""

    def __init__(
        self,
        dependencies: Mapping[str, Iterable[str]] | DependencyGraph | None = None,
        *,
        package: ClaimPackage | None = None,
    ) -> None:
        if isinstance(dependencies, DependencyGraph):
            self.dependencies = dependencies.active_mapping(package)
        else:
            self.dependencies = {
                code: tuple(targets)
                for code, targets in (dependencies or DEFAULT_DEPENDENCIES).items()
            }

    def close(self, deficiencies: Iterable[Deficiency]) -> set[Deficiency]:
        """Return the least dependency-closed deficiency set."""
        return set(self.close_ordered(deficiencies))

    def close_ordered(self, deficiencies: Iterable[Deficiency]) -> tuple[Deficiency, ...]:
        """Return dependency closure with deterministic ordering."""
        closed_items: list[Deficiency] = []
        seen_items: set[Deficiency] = set()
        present_codes: set[str] = set()
        queue: list[str] = []
        for deficiency in deficiencies:
            if deficiency not in seen_items:
                closed_items.append(deficiency)
                seen_items.add(deficiency)
            if deficiency.code not in present_codes:
                present_codes.add(deficiency.code)
                queue.append(deficiency.code)

        index = 0
        while index < len(queue):
            code = queue[index]
            index += 1
            for induced_code in self.dependencies.get(code, ()):
                if induced_code not in present_codes:
                    induced = make_deficiency(
                        induced_code,
                        message=f"Induced by dependency on {code}.",
                        depends_on=(code,),
                    )
                    closed_items.append(induced)
                    seen_items.add(induced)
                    present_codes.add(induced_code)
                    queue.append(induced_code)

        return tuple(sorted(closed_items, key=lambda item: item.sort_key()))
