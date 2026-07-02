from __future__ import annotations

from medical_drug_agent.app.debate.schemas import CandidateDebateOpinion


class DebateScorer:
    BASE_SCORE = 50

    @staticmethod
    def symptom_fit_delta(match_level: str) -> int:
        return {
            "full": 20,
            "high": 20,
            "partial": 10,
            "medium": 10,
            "none": 0,
            "insufficient": 0,
            "low": 0,
        }.get(str(match_level or "").strip().lower(), 0)

    @staticmethod
    def interaction_risk_delta(overall_risk_level: str) -> int:
        return {
            "low": 0,
            "medium": -15,
            "high": -35,
            "unknown": -5,
        }.get(str(overall_risk_level or "").strip().lower(), -5)

    @staticmethod
    def dose_delta(dose_risk_level: str) -> int:
        return {
            "missing": -5,
            "medium": -10,
            "high": -25,
            "low": 0,
            "unknown": -5,
        }.get(str(dose_risk_level or "").strip().lower(), 0)

    @classmethod
    def patient_factor_delta(
        cls,
        candidate_drug: str,
        age: int | None,
        diseases: list[str] | None = None,
        patient_factors: list[str] | None = None,
    ) -> tuple[int, list[str], list[str]]:
        delta = 0
        reasons: list[str] = []
        cautions: list[str] = []
        normalized_drug = str(candidate_drug or "").strip().lower()
        disease_text = " ".join(str(item).strip().lower() for item in list(diseases or []) if str(item).strip())
        factor_text = " ".join(
            str(item).strip().lower() for item in list(patient_factors or []) if str(item).strip()
        )

        if age is not None and age >= 65 and cls._is_ibuprofen(normalized_drug):
            delta -= 10
            reasons.append("老年人使用布洛芬类候选药时需要更加谨慎。")
            cautions.append("高龄因素提示需要进一步确认布洛芬相关胃肠道、肾脏和血压风险。")
        if "高血压" in disease_text and cls._is_ibuprofen(normalized_drug):
            delta -= 15
            reasons.append("合并高血压时，布洛芬类候选药在当前规则下风险分更高。")
            cautions.append("高血压患者使用 NSAID 时，需要结合血压控制情况进一步确认。")
        if "胃溃疡" in disease_text and cls._is_ibuprofen(normalized_drug):
            delta -= 20
            reasons.append("合并胃溃疡时，布洛芬类候选药提示更高胃肠道风险。")
            cautions.append("既往胃溃疡提示不适合自行选择 NSAID 类候选药。")
        if "肝功能异常" in disease_text and cls._is_acetaminophen(normalized_drug):
            delta -= 20
            reasons.append("合并肝功能异常时，对乙酰氨基酚类候选药需要额外谨慎。")
            cautions.append("肝功能异常时需要结合剂量和肝功能状态进一步确认。")
        if "肾功能不全" in disease_text and (
            cls._is_ibuprofen(normalized_drug) or "metformin" in normalized_drug or "二甲双胍" in normalized_drug
        ):
            delta -= 20
            reasons.append("合并肾功能不全时，该候选药在当前规则下提示更高风险。")
            cautions.append("肾功能不全提示需要医生或药师进一步确认。")
        if "pregnan" in factor_text or "妊娠" in factor_text or "怀孕" in factor_text:
            cautions.append("存在妊娠相关因素时，不应仅依赖本地排序结果，需由医生确认。")
        return delta, reasons, cautions

    @staticmethod
    def final_level(total_score: int) -> str:
        if total_score >= 70:
            return "preferred_candidate"
        if total_score >= 45:
            return "caution_candidate"
        return "not_preferred_without_review"

    @classmethod
    def total_score(cls, opinions: list[CandidateDebateOpinion]) -> int:
        return cls.BASE_SCORE + sum(int(opinion.score_delta) for opinion in opinions)

    @staticmethod
    def _is_ibuprofen(normalized_drug: str) -> bool:
        return normalized_drug in {"ibuprofen", "布洛芬"}

    @staticmethod
    def _is_acetaminophen(normalized_drug: str) -> bool:
        return normalized_drug in {"acetaminophen", "对乙酰氨基酚", "paracetamol"}
