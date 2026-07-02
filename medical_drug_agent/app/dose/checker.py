from __future__ import annotations

import pandas as pd

from medical_drug_agent.app.constants import DOSE_REFERENCE_PATH
from medical_drug_agent.app.normalization.mapper import DrugNameMapper
from medical_drug_agent.app.schemas import DoseCheckResult, DoseInput


class DoseChecker:
    """Local deterministic dose reference checker."""

    def __init__(
        self,
        mapper: DrugNameMapper | None = None,
        dose_reference_path=DOSE_REFERENCE_PATH,
    ) -> None:
        self.mapper = mapper or DrugNameMapper()
        self.dose_reference_path = dose_reference_path
        self._dose_df: pd.DataFrame | None = None

    def _get_dataframe(self) -> pd.DataFrame:
        if self._dose_df is None:
            if not self.dose_reference_path.exists():
                raise FileNotFoundError(f"剂量参考表不存在：{self.dose_reference_path}")
            self._dose_df = pd.read_csv(self.dose_reference_path).fillna("")
        return self._dose_df

    def _find_reference(self, drug_name: str) -> dict[str, str] | None:
        normalized_drug = self.mapper.normalize(drug_name)
        dataframe = self._get_dataframe()
        mask = dataframe["drug_en_name"].astype(str).str.strip().str.lower() == normalized_drug.en_name.lower()
        if not mask.any():
            return None
        return dataframe[mask].iloc[0].to_dict()

    @staticmethod
    def _coerce_float(value: object) -> float | None:
        if value in ("", None):
            return None
        return float(value)

    @staticmethod
    def _coerce_int(value: object) -> int | None:
        if value in ("", None):
            return None
        return int(float(value))

    @staticmethod
    def _has_complete_user_input(dose_input: DoseInput) -> bool:
        return (
            dose_input.single_dose_mg is not None
            and dose_input.times_per_day is not None
            and dose_input.duration_days is not None
        )

    def _build_reference_dose(self, reference: dict[str, str]) -> dict[str, int] | None:
        single_dose = self._coerce_int(reference.get("reference_single_dose_mg"))
        times_per_day = self._coerce_int(reference.get("reference_times_per_day"))
        duration_days = self._coerce_int(reference.get("reference_duration_days"))
        if single_dose is None or times_per_day is None or duration_days is None:
            return None
        return {
            "single_dose_mg": single_dose,
            "times_per_day": times_per_day,
            "duration_days": duration_days,
        }

    def check(self, dose_input: DoseInput) -> DoseCheckResult:
        try:
            reference = self._find_reference(dose_input.drug_name)
        except ValueError:
            reference = None

        reference_dose = self._build_reference_dose(reference) if reference is not None else None
        using_user_input = self._has_complete_user_input(dose_input)

        if using_user_input and reference is None:
            return DoseCheckResult(
                drug_name=dose_input.drug_name,
                status="unknown_reference",
                risk_level="unknown",
                message="当前药物暂无本地剂量参考，需由医生或药师结合说明书判断。",
                details={},
                dose_source="user_input",
                dose_source_label="用户填写剂量",
                dose_assumption_used=False,
                dose_confidence="user_provided",
                reference_dose=None,
            )

        if using_user_input:
            single_dose_mg = float(dose_input.single_dose_mg)
            times_per_day = int(dose_input.times_per_day)
            duration_days = int(dose_input.duration_days)
            dose_source = "user_input"
            dose_source_label = "用户填写剂量"
            dose_assumption_used = False
            dose_confidence = "user_provided"
        elif dose_input.allow_reference_dose and reference_dose is not None:
            single_dose_mg = float(reference_dose["single_dose_mg"])
            times_per_day = int(reference_dose["times_per_day"])
            duration_days = int(reference_dose["duration_days"])
            dose_source = "label_reference"
            dose_source_label = "说明书参考剂量"
            dose_assumption_used = True
            dose_confidence = "reference_only"
        else:
            if reference is None:
                return DoseCheckResult(
                    drug_name=dose_input.drug_name,
                    status="unknown_reference",
                    risk_level="unknown",
                    message="当前药物暂无本地剂量参考，需由医生或药师结合说明书判断。",
                    details={},
                    dose_source="missing",
                    dose_source_label="未提供剂量",
                    dose_assumption_used=False,
                    dose_confidence=None,
                    reference_dose=None,
                )

            message = "当前用药未提供实际剂量，因此未对剂量合理性进行判断。"
            if dose_input.allow_reference_dose:
                message = "未提供实际剂量，且当前药物未找到可用参考剂量，因此剂量相关判断仅作缺失提示。"
            return DoseCheckResult(
                drug_name=dose_input.drug_name,
                status="missing_dose",
                risk_level="unknown",
                message=message,
                details={},
                dose_source="missing",
                dose_source_label="未提供剂量",
                dose_assumption_used=False,
                dose_confidence=None,
                reference_dose=reference_dose,
            )

        assert reference is not None

        max_single = self._coerce_float(reference.get("max_single_dose_mg"))
        max_daily = self._coerce_float(reference.get("max_daily_dose_mg"))
        max_duration = self._coerce_int(reference.get("max_duration_days"))
        daily_dose = single_dose_mg * times_per_day

        details = {
            "reference_drug_en_name": reference.get("drug_en_name", ""),
            "reference_zh_name": reference.get("zh_name", ""),
            "max_single_dose_mg": max_single,
            "max_daily_dose_mg": max_daily,
            "max_duration_days": max_duration,
            "elderly_caution": str(reference.get("elderly_caution", "")).lower() == "true",
            "notes": reference.get("notes", ""),
            "daily_dose_mg": daily_dose,
        }

        reference_suffix = ""
        if dose_source == "label_reference":
            reference_suffix = (
                " 本次未填写实际剂量，系统基于说明书参考剂量进行初步模拟评估，"
                "不代表患者实际用药剂量，最终剂量需由医生或药师结合患者情况确认。"
            )

        if max_single is not None and single_dose_mg > max_single:
            return DoseCheckResult(
                drug_name=dose_input.drug_name,
                status="exceed_single_dose",
                risk_level="high" if single_dose_mg >= max_single * 1.5 else "medium",
                message=f"单次剂量超过本地参考上限，需要药师确认。{reference_suffix}".strip(),
                details=details,
                dose_source=dose_source,
                dose_source_label=dose_source_label,
                dose_assumption_used=dose_assumption_used,
                dose_confidence=dose_confidence,
                reference_dose=reference_dose,
            )

        if max_daily is not None and daily_dose > max_daily:
            return DoseCheckResult(
                drug_name=dose_input.drug_name,
                status="exceed_daily_dose",
                risk_level="high",
                message=f"每日总量超过本地参考上限，需要药师确认。{reference_suffix}".strip(),
                details=details,
                dose_source=dose_source,
                dose_source_label=dose_source_label,
                dose_assumption_used=dose_assumption_used,
                dose_confidence=dose_confidence,
                reference_dose=reference_dose,
            )

        if max_duration is not None and duration_days > max_duration:
            return DoseCheckResult(
                drug_name=dose_input.drug_name,
                status="long_duration_caution",
                risk_level="medium",
                message=f"用药天数超过本地短期参考，需要药师确认。{reference_suffix}".strip(),
                details=details,
                dose_source=dose_source,
                dose_source_label=dose_source_label,
                dose_assumption_used=dose_assumption_used,
                dose_confidence=dose_confidence,
                reference_dose=reference_dose,
            )

        within_reference_message = "剂量未超过本地参考上限，但仍需结合说明书和患者情况由药师确认。"
        if dose_source == "label_reference":
            within_reference_message = (
                "本次未提供实际剂量，系统基于说明书参考剂量进行了初步模拟评估。"
                "该剂量不代表患者实际用药剂量，最终剂量仍需由医生或药师结合患者情况确认。"
            )

        return DoseCheckResult(
            drug_name=dose_input.drug_name,
            status="within_reference",
            risk_level="low",
            message=within_reference_message,
            details=details,
            dose_source=dose_source,
            dose_source_label=dose_source_label,
            dose_assumption_used=dose_assumption_used,
            dose_confidence=dose_confidence,
            reference_dose=reference_dose,
        )
