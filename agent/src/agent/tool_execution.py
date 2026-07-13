"""Per-call transport contract for legacy tool text and optional metadata."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class ToolExecutionResult:
    """Immutable per-call result transport.

    ``legacy_result`` is the only value allowed into existing LLM context and
    legacy trace fields. ``execution_metadata`` is isolated per invocation for
    optional trace-only consumers; it never belongs on a reusable tool instance
    or an LLM-originated tool-call request.
    """

    legacy_result: str
    execution_metadata: Mapping[str, Any] | None = None
    transport_warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "legacy_result", _coerce_legacy_result(self.legacy_result))
        metadata, warnings = _freeze_metadata(self.execution_metadata)
        object.__setattr__(self, "execution_metadata", metadata)
        object.__setattr__(
            self,
            "transport_warnings",
            tuple(dict.fromkeys((*self.transport_warnings, *warnings))),
        )

    def with_legacy_result(self, legacy_result: Any) -> "ToolExecutionResult":
        """Keep call-bound metadata while replacing post-execution legacy text."""

        return ToolExecutionResult(
            legacy_result=_coerce_legacy_result(legacy_result),
            execution_metadata=self.execution_metadata,
            transport_warnings=self.transport_warnings,
        )


def normalize_tool_execution_result(value: Any) -> ToolExecutionResult:
    """Normalize old and new tool returns without changing legacy text.

    Existing tools return strings. Future metadata-aware tools may return
    :class:`ToolExecutionResult`. Unexpected legacy values are stringified so
    the new transport path does not introduce a new runtime exception.
    """

    if isinstance(value, ToolExecutionResult):
        return ToolExecutionResult(
            legacy_result=value.legacy_result,
            execution_metadata=value.execution_metadata,
            transport_warnings=value.transport_warnings,
        )
    return ToolExecutionResult(legacy_result=_coerce_legacy_result(value))


def _coerce_legacy_result(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def _freeze_metadata(value: Any) -> tuple[Mapping[str, Any] | None, tuple[str, ...]]:
    if value is None:
        return None, ()
    if not isinstance(value, Mapping):
        return None, ("execution_metadata_invalid",)
    return _freeze_value(dict(value)), ()


def _freeze_value(value: Any) -> Any:
    """Deep-copy and freeze common metadata containers for call isolation."""

    if isinstance(value, Mapping):
        return MappingProxyType({copy.deepcopy(key): _freeze_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze_value(item) for item in value)
    return copy.deepcopy(value)
