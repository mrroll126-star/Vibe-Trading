"""BaseTool + ToolRegistry: tool infrastructure."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)
from typing import Any, Dict, List, Optional

from src.agent.tool_execution import ToolExecutionResult, normalize_tool_execution_result


class BaseTool(ABC):
    """Tool base class.

    Attributes:
        name: Unique tool identifier.
        description: Tool description shown to the LLM.
        parameters: Parameter definition in JSON Schema format.
        repeatable: Whether the tool may be called more than once.
    """

    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}
    repeatable: bool = False
    is_readonly: bool = True

    @classmethod
    def check_available(cls) -> bool:
        """Check if this tool's dependencies are met.

        Override in subclasses to check for API keys, packages, etc.
        Tools that return False are excluded from the registry.
        """
        return True

    @abstractmethod
    def execute(self, **kwargs: Any) -> str:
        """Execute the tool and return a JSON string."""

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters or {"type": "object", "properties": {}, "required": []},
            },
        }


class ToolRegistry:
    """Tool registry."""

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def get_definitions(self) -> List[Dict[str, Any]]:
        """Return all tools in OpenAI function calling format."""
        return [t.to_openai_schema() for t in self._tools.values()]

    def execute(self, name: str, params: Dict[str, Any]) -> str:
        """Execute a tool through the legacy string-only public interface."""
        return self.execute_with_metadata(name, params).legacy_result

    def execute_with_metadata(self, name: str, params: Dict[str, Any]) -> ToolExecutionResult:
        """Execute a tool and return its isolated per-call transport result.

        This additive interface lets AgentLoop consume optional execution
        metadata without changing existing callers of :meth:`execute` or
        requiring legacy tools to migrate from their string return contract.
        """
        tool = self._tools.get(name)
        if not tool:
            return ToolExecutionResult(
                legacy_result=json.dumps(
                    {"status": "error", "error": f"Tool '{name}' not found"},
                    ensure_ascii=False,
                )
            )
        try:
            return normalize_tool_execution_result(tool.execute(**params))
        except Exception as exc:
            logger.exception("Tool %s failed", name)
            return ToolExecutionResult(
                legacy_result=json.dumps({
                    "status": "error", "tool": name,
                    "error": str(exc),
                }, ensure_ascii=False)
            )

    @property
    def tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
