from __future__ import annotations

from medical_drug_agent.app.agents.base import AgentResult, BaseAgent
from medical_drug_agent.app.audit.logger import AuditLogger


class AuditAgent(BaseAgent):
    agent_name = "audit-agent"

    def __init__(self, audit_logger: AuditLogger | None = None, enable_audit: bool = False) -> None:
        self.audit_logger = audit_logger or AuditLogger()
        self.enable_audit = enable_audit

    def run(self, state: dict) -> AgentResult:
        if not self.enable_audit:
            return AgentResult(
                agent_name=self.agent_name,
                status="skipped",
                output={"audit": {"enabled": False}},
                metadata={},
            )
        return super().run(state)

    def _run_impl(self, state: dict) -> dict:
        request_payload = dict(state.get("input_payload", {}) or {})
        response_payload = dict(state.get("response_payload", {}) or {})
        return {"audit": self.audit_logger.log_case(request_payload, response_payload)}
