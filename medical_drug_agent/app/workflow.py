from __future__ import annotations

from medical_drug_agent.app.dose.checker import DoseChecker
from medical_drug_agent.app.knowledge.local_query_engine import LocalDrugQueryEngine
from medical_drug_agent.app.normalization.mapper import DrugNameMapper
from medical_drug_agent.app.reporting.aggregator import RiskAggregator
from medical_drug_agent.app.reporting.report_generator import TemplateReportGenerator
from medical_drug_agent.app.reporting.safety_filter import SafetyFilter
from medical_drug_agent.app.rules.engine import SafetyRuleEngine
from medical_drug_agent.app.schemas import DoseInput, PatientInfo, ReportResult


class DrugSafetyWorkflow:
    """Orchestrate local normalization, KG query, rules, dose checks, aggregation, and reports."""

    def __init__(
        self,
        mapper: DrugNameMapper | None = None,
        query_engine: LocalDrugQueryEngine | None = None,
        rule_engine: SafetyRuleEngine | None = None,
        dose_checker: DoseChecker | None = None,
        aggregator: RiskAggregator | None = None,
        report_generator: TemplateReportGenerator | None = None,
        safety_filter: SafetyFilter | None = None,
    ) -> None:
        self.mapper = mapper or DrugNameMapper()
        self.query_engine = query_engine or LocalDrugQueryEngine(mapper=self.mapper)
        self.rule_engine = rule_engine or SafetyRuleEngine()
        self.dose_checker = dose_checker or DoseChecker(mapper=self.mapper)
        self.aggregator = aggregator or RiskAggregator()
        self.report_generator = report_generator or TemplateReportGenerator()
        self.safety_filter = safety_filter or SafetyFilter()

    def run(
        self,
        current_drugs: list[str],
        new_drug: str,
        age: int | None = None,
        diseases: list[str] | None = None,
        patient_factors: list[str] | None = None,
        dose_inputs: list[DoseInput] | None = None,
    ) -> ReportResult:
        normalized_current = self.mapper.normalize_many(current_drugs)
        normalized_new = self.mapper.normalize(new_drug)
        patient = PatientInfo(
            age=age,
            diseases=diseases or [],
            patient_factors=patient_factors or [],
        )

        current_pair_relations = []
        for current_drug in current_drugs:
            current_pair_relations.extend(self.query_engine.query_drug_pair(current_drug, new_drug))

        rule_matches = self.rule_engine.match_rules(
            current_drugs=normalized_current,
            new_drug=normalized_new,
            patient=patient,
        )

        effective_dose_inputs = dose_inputs or [DoseInput(drug_name=new_drug)]
        dose_results = [self.dose_checker.check(item) for item in effective_dose_inputs]

        risk_summary = self.aggregator.aggregate(
            current_drugs=normalized_current,
            new_drug=normalized_new,
            kg_pair_relations=current_pair_relations,
            rule_matches=rule_matches,
            dose_results=dose_results,
        )

        pharmacist_report, patient_report = self.report_generator.generate(
            current_drugs=normalized_current,
            new_drug=normalized_new,
            patient=patient,
            risk_summary=risk_summary,
        )

        pharmacist_report, warnings_a = self.safety_filter.validate_and_fix(pharmacist_report)
        patient_report, warnings_b = self.safety_filter.validate_and_fix(patient_report)

        return ReportResult(
            pharmacist_report=pharmacist_report,
            patient_report=patient_report,
            risk_summary=risk_summary,
            safety_warnings=warnings_a + warnings_b,
        )

