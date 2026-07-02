from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CandidateDebateOpinion:
    candidate_drug: str
    agent_name: str
    score_delta: int
    risk_level: str
    opinion: str
    reasons: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CandidateDebateResult:
    candidate_drug: str
    total_score: int
    rank: int
    final_level: str
    summary: str
    strengths: list[str] = field(default_factory=list)
    cautions: list[str] = field(default_factory=list)
    agent_opinions: list[CandidateDebateOpinion] = field(default_factory=list)


@dataclass(slots=True)
class MedicationDebateSummary:
    debate_enabled: bool
    red_flag_blocked: bool
    ranked_candidates: list[str] = field(default_factory=list)
    conclusion: str = ""
    disclaimer: str = ""
