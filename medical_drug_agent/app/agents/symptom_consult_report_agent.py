from __future__ import annotations

from medical_drug_agent.app.agents.base import BaseAgent
from medical_drug_agent.app.debate.report_builder import build_debate_report_lines


class SymptomConsultReportAgent(BaseAgent):
    agent_name = "symptom-consult-report-agent"

    DISCLAIMER_1 = "本报告仅为症状问诊辅助参考，不构成诊断或处方建议。"
    DISCLAIMER_2 = "以下内容仅供医生或药师进行 OTC 候选药辅助评估参考，是否适合使用仍需结合个体情况、药品说明书和专业判断。"
    DISCLAIMER_3 = "以上候选药排序仅表示在当前本地规则、症状匹配和药物安全检查结果下的辅助评估，不构成诊断或处方建议，最终用药需由医生或药师确认。"
    DOSE_REFERENCE_NOTE = (
        "本次未提供实际剂量，系统基于说明书参考剂量进行了初步模拟评估。"
        "该剂量不代表患者实际用药剂量，最终剂量仍需由医生或药师结合患者情况确认。"
    )
    DOSE_MISSING_NOTE = "未提供实际剂量，且当前药物未找到可用参考剂量，因此剂量相关判断仅作缺失提示。"

    def _run_impl(self, state: dict) -> dict:
        payload = dict(state.get("input_payload", {}) or {})
        red_flags = list(state.get("red_flags", []) or [])
        disease_candidates = list(state.get("disease_candidates", []) or [])
        referral_required = bool(state.get("referral_required"))
        disease_match_summary = str(state.get("disease_match_summary", "") or "").strip()
        otc_candidates = list(state.get("otc_candidates", []) or [])
        candidate_safety_results = list(state.get("candidate_safety_results", []) or [])
        debate_results = list(state.get("debate_results", []) or [])
        debate_summary = state.get("medication_debate_summary")

        lines = [
            "症状问诊辅助报告",
            "",
            f"症状描述：{str(payload.get('symptom_text', '') or '').strip()}",
            f"年龄：{payload.get('age') if payload.get('age') is not None else '未提供'}",
            f"体温：{payload.get('temperature_c') if payload.get('temperature_c') is not None else '未提供'}",
            f"持续天数：{payload.get('duration_days') if payload.get('duration_days') is not None else '未提供'}",
            "",
            "红旗症状筛查：",
        ]

        if red_flags:
            for finding in red_flags:
                lines.append(f"- [{finding.urgency_level}] {finding.description}；处理提示：{finding.action}")
            lines.extend(
                [
                    "",
                    "当前描述涉及严重疾病或红旗风险，不适合由本系统生成 OTC 候选药，请由医生进一步评估。",
                    "",
                    self.DISCLAIMER_1,
                    self.DISCLAIMER_2,
                    self.DISCLAIMER_3,
                ]
            )
            return {"consult_report": "\n".join(lines)}

        lines.extend(["", "常见疾病候选："])
        lines.append("以下为基于症状关键词匹配得到的常见疾病候选，仅用于问诊辅助，不构成诊断。")
        if disease_candidates:
            for candidate in disease_candidates:
                keywords = "、".join(list(getattr(candidate, "matched_keywords", []) or [])) or "暂无"
                caution = "；需谨慎评估" if getattr(candidate, "scope", "") == "otc_caution" else ""
                lines.append(
                    f"- {getattr(candidate, 'disease_name_cn', '')}：匹配 {keywords}；"
                    f"范围 {getattr(candidate, 'scope', '')}{caution}。"
                )
        else:
            lines.append("- 未匹配到明确常见病候选，仅基于症状规则进行初步辅助评估。")

        if disease_match_summary:
            lines.append(f"- {disease_match_summary}")

        if referral_required:
            lines.extend(
                [
                    "",
                    "当前描述涉及严重疾病或红旗风险，不适合由本系统生成 OTC 候选药，请由医生进一步评估。",
                    "",
                    self.DISCLAIMER_1,
                    self.DISCLAIMER_2,
                    self.DISCLAIMER_3,
                ]
            )
            return {"consult_report": "\n".join(lines)}

        lines.extend(
            [
                "- 当前未触发明确红旗阻断，可继续进行 OTC 候选药辅助评估。",
                "",
                "OTC 候选药：",
            ]
        )
        if otc_candidates:
            for candidate in otc_candidates:
                lines.append(
                    f"- {candidate.drug_class}：候选药 {', '.join(candidate.candidate_drugs)}；注意事项："
                    f"{candidate.caution or '请结合说明书和个体情况进一步确认。'}"
                )
        else:
            lines.append("- 当前症状不在本系统面向社区药店轻症场景的 OTC 候选范围内。")

        lines.extend(["", "候选药安全检查摘要："])
        if candidate_safety_results:
            for result in candidate_safety_results:
                response = result.safety_response or {}
                data = response.get("data") or {}
                status = response.get("status")
                dose_result = (data.get("dose_results") or [{}])[0]
                dose_source_label = str(dose_result.get("dose_source_label", "") or "未提供剂量")
                dose_message = str(dose_result.get("message", "") or "").strip()

                if status == "success":
                    lines.append(
                        f"- {result.candidate_drug}：综合风险等级 {data.get('overall_risk_level')}；"
                        f"剂量来源：{dose_source_label}。"
                    )
                    if dose_result.get("dose_source") == "label_reference":
                        lines.append(f"  {self.DOSE_REFERENCE_NOTE}")
                    elif dose_result.get("dose_source") == "missing" and dose_result.get("status") == "missing_dose":
                        lines.append(f"  {self.DOSE_MISSING_NOTE}")
                    if dose_message:
                        lines.append(f"  剂量提示：{dose_message}")
                else:
                    lines.append(f"- {result.candidate_drug}：未完成候选药安全检查，请由医生或药师进一步评估。")
        else:
            lines.append("- 当前没有可展示的候选药安全检查结果。")

        if not list(payload.get("current_drugs", []) or []):
            lines.extend(
                [
                    "",
                    "当前未提供当前用药，因此未进行药物-药物相互作用检查；系统仍已结合疾病、过敏史、特殊人群和剂量信息进行初步评估。",
                ]
            )

        if not isinstance(payload.get("dose"), dict):
            lines.extend(["", self.DOSE_REFERENCE_NOTE])

        lines.extend([""])
        lines.extend(build_debate_report_lines(debate_summary, debate_results, red_flag_triggered=False))
        lines.extend(["", self.DISCLAIMER_1, self.DISCLAIMER_2, self.DISCLAIMER_3])
        return {"consult_report": "\n".join(lines)}
