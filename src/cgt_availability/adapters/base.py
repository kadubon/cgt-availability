"""Shared optional-adapter exceptions and records."""

from __future__ import annotations

from dataclasses import dataclass, field

from cgt_availability.core.serialization import JSONValue, ensure_json_object


class AdapterUnavailable(RuntimeError):
    """Raised when an optional library or external binary is unavailable."""


class AdapterExecutionError(RuntimeError):
    """Raised when an optional adapter is available but execution fails."""


@dataclass(frozen=True)
class AdapterErrorRecord:
    """Serializable adapter failure record for interop fixtures and CLI surfaces."""

    adapter: str
    error_type: str
    message: str
    command: tuple[str, ...] = ()
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    @classmethod
    def from_exception(
        cls,
        adapter: str,
        exc: BaseException,
        *,
        command: tuple[str, ...] = (),
        metadata: dict[str, JSONValue] | None = None,
    ) -> AdapterErrorRecord:
        """Build a portable error record from an adapter exception."""
        return cls(
            adapter=adapter,
            error_type=type(exc).__name__,
            message=str(exc),
            command=command,
            metadata={} if metadata is None else metadata,
        )

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)
