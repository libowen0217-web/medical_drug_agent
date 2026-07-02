from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DrugInfo:
    input_name: str
    zh_name: str
    en_name: str
    aliases: list[str] = field(default_factory=list)
    drug_class: str = ""
    notes: str = ""


@dataclass(slots=True)
class DrugRelation:
    x_name: str
    x_type: str
    y_name: str
    y_type: str
    relation: str
    display_relation: str
    keep_reason: str
    matched_core_drug: str
    source_row: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class QueryResult:
    drug_name: str
    normalized_drug: DrugInfo
    drug_drug_relations: list[DrugRelation] = field(default_factory=list)
    drug_disease_relations: list[DrugRelation] = field(default_factory=list)
    drug_effect_relations: list[DrugRelation] = field(default_factory=list)
    total_count: int = 0


@dataclass(slots=True)
class PatientInfo:
    age: int | None = None
    diseases: list[str] = field(default_factory=list)
    patient_factors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RuleMatch:
    rule_id: str
    risk_level: str
    risk: str
    mechanism: str
    recommendation: str
    evidence_note: str
    matched_reason: str


@dataclass(slots=True)
class DoseInput:
    drug_name: str
    single_dose_mg: float | None = None
    times_per_day: int | None = None
    duration_days: int | None = None
    dose_mode: str | None = None
    allow_reference_dose: bool = False
    dose_context: str | None = None


@dataclass(slots=True)
class DoseCheckResult:
    drug_name: str
    status: str
    risk_level: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    dose_source: str = "missing"
    dose_source_label: str = "未提供剂量"
    dose_assumption_used: bool = False
    dose_confidence: str | None = None
    reference_dose: dict[str, Any] | None = None


@dataclass(slots=True)
class EvidenceItem:
    evidence_id: str
    topic: str
    source_type: str
    source_name: str
    evidence_text: str
    matched_reason: str
    score: float = 0.0
    rank: int | None = None
    citation_label: str | None = None
    matched_keywords: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RiskFinding:
    source: str
    risk_level: str
    title: str
    description: str
    mechanism: str
    recommendation: str
    evidence_note: str
    related_drugs: list[str] = field(default_factory=list)
    related_diseases: list[str] = field(default_factory=list)
    evidence_items: list[EvidenceItem] = field(default_factory=list)


@dataclass(slots=True)
class RiskSummary:
    overall_risk_level: str
    findings: list[RiskFinding] = field(default_factory=list)
    rule_matches: list[RuleMatch] = field(default_factory=list)
    dose_results: list[DoseCheckResult] = field(default_factory=list)
    kg_relation_count: int = 0
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ReportResult:
    pharmacist_report: str
    patient_report: str
    risk_summary: RiskSummary
    safety_warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DrugSafetyRequest:
    current_drugs: list[str] = field(default_factory=list)
    new_drug: str = ""
    age: int | None = None
    diseases: list[str] = field(default_factory=list)
    patient_factors: list[str] = field(default_factory=list)
    dose: dict[str, Any] | None = None


@dataclass(slots=True)
class DrugSafetyResponse:
    request_id: str
    timestamp: str
    status: str
    error_code: str | None
    message: str
    data: dict[str, Any] | None
    metadata: dict[str, Any] = field(default_factory=dict)
