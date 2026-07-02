from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AgentResult:
    agent_name: str
    status: str
    output: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent:
    agent_name: str = "base-agent"

    def run(self, state: dict[str, Any]) -> AgentResult:
        try:
            output = self._run_impl(state)
            return AgentResult(
                agent_name=self.agent_name,
                status="success",
                output=output or {},
                metadata={},
            )
        except FileNotFoundError as exc:
            return AgentResult(
                agent_name=self.agent_name,
                status="error",
                error=str(exc),
                metadata={"error_code": "DATA_FILE_MISSING"},
            )
        except ValueError as exc:
            return AgentResult(
                agent_name=self.agent_name,
                status="error",
                error=str(exc),
                metadata={"error_code": "UNKNOWN_DRUG"},
            )
        except Exception as exc:
            return AgentResult(
                agent_name=self.agent_name,
                status="error",
                error=str(exc),
                metadata={"error_code": "WORKFLOW_ERROR"},
            )

    def _run_impl(self, state: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
