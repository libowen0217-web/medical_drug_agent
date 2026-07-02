from __future__ import annotations

from medical_drug_agent.app.debate.schemas import CandidateDebateResult, MedicationDebateSummary


def build_debate_report_lines(
    summary: MedicationDebateSummary | None,
    debate_results: list[CandidateDebateResult] | None,
    red_flag_triggered: bool,
) -> list[str]:
    lines = ["候选药协作评估："]
    if red_flag_triggered:
        lines.append("- 已触发红旗症状，本轮不展示候选药排序，建议及时就医或由医生进一步评估。")
        if summary and summary.disclaimer:
            lines.append(f"- {summary.disclaimer}")
        return lines

    results = list(debate_results or [])
    if not results:
        lines.append("- 当前没有可用于协作评估的候选药排序结果。")
        if summary and summary.disclaimer:
            lines.append(f"- {summary.disclaimer}")
        return lines

    for item in results:
        lines.append(f"- 排名 {item.rank}: {item.candidate_drug} | level={item.final_level} | score={item.total_score}")
        if item.strengths:
            lines.append(f"  支持点：{'; '.join(item.strengths[:2])}")
        if item.cautions:
            lines.append(f"  注意点：{'; '.join(item.cautions[:2])}")
    if summary and summary.conclusion:
        lines.append(f"- 结论：{summary.conclusion}")
    if summary and summary.disclaimer:
        lines.append(f"- {summary.disclaimer}")
    return lines
