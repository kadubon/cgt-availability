"""External-process model-checking adapter boundary."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from cgt_availability.adapters.base import AdapterExecutionError, AdapterUnavailable
from cgt_availability.core.serialization import JSONValue, ensure_json_object


class ModelCheckerOutputMode(StrEnum):
    """Supported external model-checker output parsing modes."""

    TEXT = "text"
    JSON = "json"


@dataclass(frozen=True)
class ExternalModelCheckResult:
    """Result returned by an external model-checking command."""

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    parsed: dict[str, JSONValue] | None = None
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


@dataclass(frozen=True)
class ExternalModelCheckerAdapter:
    """Adapter for tools such as PRISM or Storm without bundling them."""

    command: str
    timeout_seconds: float = 30.0

    def run(
        self,
        arguments: tuple[str, ...],
        *,
        parse_json: bool = False,
    ) -> ExternalModelCheckResult:
        """Run an explicit external model-checker command line."""
        executable = shutil.which(self.command)
        if executable is None:
            raise AdapterUnavailable(
                f"model-checker command is unavailable: {self.command!r}"
            )
        command = [executable, *arguments]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except OSError as exc:
            raise AdapterExecutionError(str(exc)) from exc
        except subprocess.TimeoutExpired as exc:
            raise AdapterExecutionError(
                f"model-checker command timed out after {self.timeout_seconds}s"
            ) from exc
        if completed.returncode != 0:
            raise AdapterExecutionError(
                f"model-checker command failed with code {completed.returncode}: "
                f"{completed.stderr.strip()}"
            )
        parsed = _parse_json_object(completed.stdout) if parse_json else None
        return ExternalModelCheckResult(
            command=tuple(command),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            parsed=parsed,
            metadata={"adapter": "external_process"},
        )

    def check_model(
        self,
        model_path: str | Path,
        *,
        property_path: str | Path | None = None,
        args: tuple[str, ...] = (),
        parse_json: bool = False,
    ) -> ExternalModelCheckResult:
        command = [str(model_path), *args]
        if property_path is not None:
            command.append(str(property_path))
        return self.run(tuple(command), parse_json=parse_json)


@dataclass(frozen=True)
class ModelCheckerCommandProfile:
    """Portable command-construction profile for an external checker."""

    name: str
    command: str
    default_args: tuple[str, ...] = ()
    property_flag: str | None = None
    output_mode: ModelCheckerOutputMode = ModelCheckerOutputMode.TEXT
    timeout_seconds: float = 30.0
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    def build_arguments(
        self,
        model_path: str | Path,
        property_path: str | Path | None = None,
        *,
        args: tuple[str, ...] = (),
    ) -> tuple[str, ...]:
        """Build checker arguments without resolving or executing the binary."""
        arguments: list[str] = [*self.default_args, str(model_path)]
        if property_path is not None:
            if self.property_flag is None:
                arguments.append(str(property_path))
            else:
                arguments.extend((self.property_flag, str(property_path)))
        arguments.extend(args)
        return tuple(arguments)

    def adapter(self) -> ExternalModelCheckerAdapter:
        """Return an external-process adapter for this command profile."""
        return ExternalModelCheckerAdapter(
            self.command,
            timeout_seconds=self.timeout_seconds,
        )

    def check_model(
        self,
        model_path: str | Path,
        *,
        property_path: str | Path | None = None,
        args: tuple[str, ...] = (),
    ) -> ExternalModelCheckResult:
        """Execute the configured profile through an external-process adapter."""
        return self.adapter().run(
            self.build_arguments(model_path, property_path, args=args),
            parse_json=self.output_mode == ModelCheckerOutputMode.JSON,
        )

    def to_dict(self) -> dict[str, JSONValue]:
        return ensure_json_object(self)


def _parse_json_object(value: str) -> dict[str, JSONValue]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise AdapterExecutionError(f"invalid JSON output: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise AdapterExecutionError("external model checker JSON output must be an object")
    return parsed


PRISM_COMMAND_PROFILE = ModelCheckerCommandProfile(
    name="prism",
    command="prism",
    metadata={
        "license_boundary": "external_process",
        "notes": "PRISM is not vendored or declared as a Python dependency.",
    },
)

STORM_COMMAND_PROFILE = ModelCheckerCommandProfile(
    name="storm",
    command="storm",
    default_args=("--prism",),
    property_flag="--prop",
    metadata={
        "license_boundary": "external_process",
        "notes": "Storm is not vendored or declared as a Python dependency.",
    },
)
