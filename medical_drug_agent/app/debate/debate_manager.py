from __future__ import annotations

from medical_drug_agent.app.debate.schemas import (
    CandidateDebateOpinion,
    CandidateDebateResult,
    MedicationDebateSummary,
)
from medical_drug_agent.app.debate.scoring import DebateScorer


class MedicationDebateManager:
    DISCLAIMER = (
        "以上候选药排序仅表示在当前本地规则、症状匹配和药物安全检查结果下的辅助评估，"
        "不构成诊断或处方建议，最终用药需由医生或药师确认。"
    )

    def aggregate(
        self,
        opinions_by_candidate: dict[str, list[CandidateDebateOpinion]],
        red_flag_blocked: bool = False,
    ) -> tuple[MedicationDebateSummary, list[CandidateDebateResult]]:
        if red_flag_blocked:
            summary = MedicationDebateSummary(
                debate_enabled=False,
                red_flag_blocked=True,
                ranked_candidates=[],
                conclusion="已触发红旗症状，当前不进入候选药协作评估与排序流程，建议及时就医或由医生进一步评估。",
                disclaimer=self.DISCLAIMER,
            )
            return summary, []

        results: list[CandidateDebateResult] = []
        for candidate_drug, opinions in opinions_by_candidate.items():
            total_score = DebateScorer.total_score(opinions)
            final_level = DebateScorer.final_level(total_score)
            strengths = self._collect_points(opinions, positive=True)
            cautions = self._collect_points(opinions, positive=False)
            summary = self._build_candidate_summary(candidate_drug, final_level, strengths, cautions)
            results.append(
                CandidateDebateResult(
                    candidate_drug=candidate_drug,
                    total_score=total_score,
                    rank=0,
                    final_level=final_level,
                    summary=summary,
                    strengths=strengths,
                    cautions=cautions,
                    agent_opinions=opinions,
                )
            )

        results.sort(
            key=lambda item: (
                -item.total_score,
                self._risk_priority(item.agent_opinions),
                item.candidate_drug,
            )
        )
        for index, item in enumerate(results, start=1):
            item.rank = index

        top_text = "当前没有可排序的候选药。"
        if results:
            top_names = "、".join(item.candidate_drug for item in results[:3])
            top_text = (
                f"当前排序靠前的候选药为：{top_names}。这些结果仅表示在本地规则下的相对较低风险候选方向，"
                "仍需由医生或药师结合个体情况确认。"
            )

        summary = MedicationDebateSummary(
            debate_enabled=bool(results),
            red_flag_blocked=False,
            ranked_candidates=[item.candidate_drug for item in results],
            conclusion=top_text,
            disclaimer=self.DISCLAIMER,
        )
        return summary, results

    @staticmethod
    def _collect_points(opinions: list[CandidateDebateOpinion], positive: bool) -> list[str]:
        points: list[str] = []
        for opinion in opinions:
            if positive and opinion.score_delta > 0:
                points.extend(opinion.reasons)
            if not positive and (opinion.score_delta < 0 or opinion.risk_level in {"medium", "high", "unknown"}):
                points.extend(opinion.reasons)
        seen: set[str] = set()
        deduped: list[str] = []
        for point in points:
            if point and point not in seen:
                seen.add(point)
                deduped.append(point)
        return deduped

    @staticmethod
    def _build_candidate_summary(
        candidate_drug: str,
        final_level: str,
        strengths: list[str],
        cautions: list[str],
    ) -> str:
        level_text = {
            "preferred_candidate": "在当前本地规则下属于相对较低风险候选方向",
            "caution_candidate": "在当前本地规则下需要谨慎复核",
            "not_preferred_without_review": "在当前本地规则下不宜优先考虑，需进一步复核",
        }.get(final_level, "需要进一步复核")
        summary = f"{candidate_drug} {level_text}。"
        if strengths:
            summary += f" 主要支持点：{strengths[0]}"
        if cautions:
            summary += f" 主要注意点：{cautions[0]}"
        return summary

    @staticmethod
    def _risk_priority(opinions: list[CandidateDebateOpinion]) -> int:
        priorities = {"low": 0, "unknown": 1, "medium": 2, "high": 3}
        return max((priorities.get(opinion.risk_level, 1) for opinion in opinions), default=1)
