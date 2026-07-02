from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from medical_drug_agent.app.debate.schemas import CandidateDebateResult, MedicationDebateSummary


@dataclass(slots=True)
class SymptomConsultRequest:
    symptom_text: str
    age: int | None = None
    sex: str | None = None
    temperature_c: float | None = None
    duration_days: int | None = None
    current_drugs: list[str] = field(default_factory=list)
    diseases: list[str] = field(default_factory=list)
    patient_factors: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParsedSymptom:
    symptom_name: str
    matched_keywords: list[str] = field(default_factory=list)
    severity: str | None = None


@dataclass(slots=True)
class RedFlagFinding:
    red_flag_id: str
    title: str
    description: str
    matched_keywords: list[str] = field(default_factory=list)
    action: str = ""
    urgency_level: str = ""


@dataclass(slots=True)
class DiseaseCandidate:
    disease_id: str
    disease_name_cn: str
    disease_name_en: str = ""
    category: str = ""
    scope: str = ""
    severity: str = ""
    typical_symptoms: list[str] = field(default_factory=list)
    matched_keywords: list[str] = field(default_factory=list)
    candidate_drug_classes: list[str] = field(default_factory=list)
    candidate_drugs: list[str] = field(default_factory=list)
    advice: str = ""
    score: int = 0


@dataclass(slots=True)
class OTCCandidate:
    candidate_id: str
    symptom_group: str
    drug_class: str
    candidate_drugs: list[str] = field(default_factory=list)
    is_otc: bool = True
    requires_doctor_confirmation: bool = False
    caution: str = ""
    reason: str = ""
    source: str = "symptom_rule"
    source_disease: str = ""
    source_disease_id: str = ""


@dataclass(slots=True)
class CandidateSafetyResult:
    candidate_drug: str
    safety_response: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SymptomConsultResult:
    parsed_symptoms: list[ParsedSymptom] = field(default_factory=list)
    red_flags: list[RedFlagFinding] = field(default_factory=list)
    disease_candidates: list[DiseaseCandidate] = field(default_factory=list)
    referral_required: bool = False
    disease_match_summary: str = ""
    otc_candidates: list[OTCCandidate] = field(default_factory=list)
    candidate_safety_results: list[CandidateSafetyResult] = field(default_factory=list)
    debate_results: list[CandidateDebateResult] = field(default_factory=list)
    medication_debate_summary: MedicationDebateSummary | None = None
    consult_report: str = ""
