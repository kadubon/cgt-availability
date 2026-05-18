"""Serialization helpers for JSON-compatible CGT availability objects."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, TypeAlias, cast

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
JSONObject: TypeAlias = dict[str, JSONValue]


def to_json_value(value: object) -> JSONValue:
    """Convert supported values to a JSON-compatible structure."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Enum):
        return cast(JSONScalar, value.value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: to_json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple | list):
        return [to_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_json_value(item) for key, item in value.items()}
    raise TypeError(f"Unsupported JSON value: {type(value).__name__}")


def ensure_json_object(value: object) -> JSONObject:
    """Return a JSON object or raise a clear type error."""
    json_value = to_json_value(value)
    if not isinstance(json_value, dict):
        raise TypeError("Expected a JSON object")
    return json_value


def json_dumps(value: object, *, indent: int | None = None) -> str:
    """Serialize an object with stable key ordering."""
    return json.dumps(to_json_value(value), indent=indent, sort_keys=True)


def json_loads_object(data: str) -> dict[str, Any]:
    """Load a JSON object from text."""
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def string_tuple(value: object) -> tuple[str, ...]:
    """Coerce a JSON array or scalar string into a tuple of strings."""
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, tuple | list):
        return tuple(str(item) for item in value)
    return (str(value),)


def string_dict(value: object) -> dict[str, JSONValue]:
    """Coerce mapping-like metadata into a JSON-compatible dict."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise TypeError("Expected metadata to be a mapping")
    return cast(dict[str, JSONValue], to_json_value(value))
