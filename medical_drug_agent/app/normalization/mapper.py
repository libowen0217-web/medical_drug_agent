from __future__ import annotations

from dataclasses import replace

import pandas as pd

from medical_drug_agent.app.constants import DRUG_NAME_MAP_PATH
from medical_drug_agent.app.schemas import DrugInfo


class DrugNameMapper:
    """Normalize Chinese, English, and alias drug names into canonical drug info."""

    def __init__(self, map_path=DRUG_NAME_MAP_PATH) -> None:
        self.map_path = map_path
        self._drug_infos: list[DrugInfo] = []
        self._lookup: dict[str, DrugInfo] = {}
        self._load()

    @staticmethod
    def _normalize_key(value: str) -> str:
        return value.strip().lower()

    @staticmethod
    def _parse_aliases(raw_value: object) -> list[str]:
        if pd.isna(raw_value) or raw_value is None:
            return []
        return [part.strip() for part in str(raw_value).split("|") if part.strip()]

    def _register(self, key: str, drug_info: DrugInfo) -> None:
        normalized = self._normalize_key(key)
        if normalized:
            self._lookup[normalized] = drug_info

    def _load(self) -> None:
        if not self.map_path.exists():
            raise FileNotFoundError(f"药名映射表不存在：{self.map_path}")

        dataframe = pd.read_csv(self.map_path)
        required_columns = {"zh_name", "en_name", "aliases", "drug_class", "notes"}
        missing_columns = required_columns.difference(dataframe.columns)
        if missing_columns:
            raise ValueError(f"药名映射表缺少字段：{sorted(missing_columns)}")

        for row in dataframe.fillna("").to_dict(orient="records"):
            aliases = self._parse_aliases(row.get("aliases", ""))
            drug_info = DrugInfo(
                input_name="",
                zh_name=str(row["zh_name"]).strip(),
                en_name=str(row["en_name"]).strip(),
                aliases=aliases,
                drug_class=str(row.get("drug_class", "")).strip(),
                notes=str(row.get("notes", "")).strip(),
            )
            self._drug_infos.append(drug_info)
            self._register(drug_info.zh_name, drug_info)
            self._register(drug_info.en_name, drug_info)
            for alias in aliases:
                self._register(alias, drug_info)

    def normalize(self, name: str) -> DrugInfo:
        normalized_name = self._normalize_key(name)
        if not normalized_name:
            raise ValueError("未识别药物：，请先补充药名映射表")

        drug_info = self._lookup.get(normalized_name)
        if drug_info is None:
            raise ValueError(f"未识别药物：{name}，请先补充药名映射表")

        return replace(drug_info, input_name=name.strip())

    def normalize_many(self, names: list[str]) -> list[DrugInfo]:
        return [self.normalize(name) for name in names]

    def list_supported_drugs(self) -> list[DrugInfo]:
        return [replace(drug_info) for drug_info in self._drug_infos]
