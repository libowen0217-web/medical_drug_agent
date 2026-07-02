from __future__ import annotations

from medical_drug_agent.app.agents.base import BaseAgent
from medical_drug_agent.app.reporting.report_generator import TemplateReportGenerator


class ReportAgent(BaseAgent):
    agent_name = "report-agent"

    def __init__(self, report_generator: TemplateReportGenerator | None = None) -> None:
        self.report_generator = report_generator or TemplateReportGenerator()

    def _run_impl(self, state: dict) -> dict:
        pharmacist_report, patient_report = self.report_generator.generate(
            current_drugs=list(state.get("normalized_current_drugs", []) or []),
            new_drug=state.get("normalized_new_drug"),
            patient=state.get("patient_info"),
            risk_summary=state.get("risk_summary"),
        )
        return {
            "pharmacist_report": pharmacist_report,
            "patient_report": patient_report,
        }
