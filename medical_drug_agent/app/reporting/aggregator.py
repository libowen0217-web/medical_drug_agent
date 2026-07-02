from __future__ import annotations

from medical_drug_agent.app.evidence.retriever import EvidenceRetriever
from medical_drug_agent.app.schemas import (
    DoseCheckResult,
    DrugInfo,
    DrugRelation,
    RiskFinding,
    RiskSummary,
    RuleMatch,
)


class RiskAggregator:
    """Aggregate KG relations, rule matches, dose checks, and local evidence."""

    DOSE_TITLES = {
        "missing_dose": "剂量信息缺失",
        "exceed_single_dose": "单次剂量超过本地参考上限",
        "exceed_daily_dose": "每日总量超过本地参考上限",
        "long_duration_caution": "用药天数超过本地短期参考",
        "unknown_reference": "暂无本地剂量参考",
        "within_reference": "剂量未超过本地参考上限",
    }

    RISK_ORDER = {"high": 3, "medium": 2, "low": 1, "unknown": 0}

    def __init__(
        self,
        enable_evidence: bool = True,
        evidence_retriever: EvidenceRetriever | None = None,
    ) -> None:
        self.enable_evidence = enable_evidence
        self.evidence_retriever = evidence_retriever or EvidenceRetriever()

    def aggregate(
        self,
        current_drugs: list[DrugInfo],
        new_drug: DrugInfo,
        kg_pair_relations: list[DrugRelation],
        rule_matches: list[RuleMatch],
        dose_results: list[DoseCheckResult],
    ) -> RiskSummary:
        findings: list[RiskFinding] = []
        notes: list[str] = []

        for match in rule_matches:
            findings.append(
                RiskFinding(
                    source="rule_match",
                    risk_level=match.risk_level,
                    title=match.risk,
                    description=match.matched_reason,
                    mechanism=match.mechanism,
                    recommendation=match.recommendation,
                    evidence_note=match.evidence_note,
                    related_drugs=[drug.zh_name for drug in current_drugs] + [new_drug.zh_name],
                    related_diseases=[],
                    evidence_items=self._safe_rule_evidence(match, notes),
                )
            )

        for dose_result in dose_results:
            findings.append(
                RiskFinding(
                    source="dose_check",
                    risk_level=dose_result.risk_level,
                    title=self.DOSE_TITLES.get(dose_result.status, "剂量检查结果"),
                    description=dose_result.message,
                    mechanism="基于本地剂量参考表的确定性检查结果",
                    recommendation="需要药师结合说明书和患者情况确认",
                    evidence_note="本地剂量参考表",
                    related_drugs=[dose_result.drug_name],
                    related_diseases=[],
                    evidence_items=self._safe_dose_evidence(dose_result, notes),
                )
            )

        if kg_pair_relations:
            findings.append(
                RiskFinding(
                    source="kg_relation",
                    risk_level="unknown",
                    title="存在知识图谱药物关系",
                    description="在 PrimeKG 本地数据集中检索到当前药物与新增药物存在直接关系",
                    mechanism="该关系表示知识图谱中存在关联记录，但未单独给出临床风险等级",
                    recommendation="该关系仅表示知识图谱中存在关联，不能单独作为临床风险等级判断依据，需结合规则和药师判断",
                    evidence_note="PrimeKG 本地 CSV 子集",
                    related_drugs=[drug.zh_name for drug in current_drugs] + [new_drug.zh_name],
                    related_diseases=[],
                    evidence_items=[],
                )
            )
            notes.append("已检索到当前药物与新增药物的直接知识图谱关系。")

        deduped_findings = self._dedupe(findings)
        overall_risk_level = self._overall_risk_level(deduped_findings)

        return RiskSummary(
            overall_risk_level=overall_risk_level,
            findings=deduped_findings,
            rule_matches=rule_matches,
            dose_results=dose_results,
            kg_relation_count=len(kg_pair_relations),
            notes=notes,
        )

    def _dedupe(self, findings: list[RiskFinding]) -> list[RiskFinding]:
        deduped: dict[tuple[str, str, tuple[str, ...]], RiskFinding] = {}
        for finding in findings:
            key = (
                finding.source,
                finding.title,
                tuple(sorted(finding.related_drugs)),
            )
            if key not in deduped:
                deduped[key] = finding
        return list(deduped.values())

    def _overall_risk_level(self, findings: list[RiskFinding]) -> str:
        highest = "unknown"
        for finding in findings:
            if self.RISK_ORDER.get(finding.risk_level, 0) > self.RISK_ORDER.get(highest, 0):
                highest = finding.risk_level
        return highest

    def _safe_rule_evidence(self, match: RuleMatch, notes: list[str]):
        if not self.enable_evidence:
            return []
        try:
            return self.evidence_retriever.retrieve_for_rule_match(match)
        except Exception as exc:
            notes.append(f"证据检索失败(rule_match:{match.rule_id})：{exc}")
            return []

    def _safe_dose_evidence(self, dose_result: DoseCheckResult, notes: list[str]):
        if not self.enable_evidence:
            return []
        try:
            return self.evidence_retriever.retrieve_for_dose_result(dose_result)
        except Exception as exc:
            notes.append(f"证据检索失败(dose_check:{dose_result.drug_name})：{exc}")
            return []
