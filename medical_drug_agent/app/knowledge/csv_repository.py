from __future__ import annotations

import pandas as pd

from medical_drug_agent.app.constants import PROCESSED_DATA_PATH


class PrimeKGCSVRepository:
    """Repository for the processed PrimeKG CSV subset."""

    def __init__(self, csv_path=PROCESSED_DATA_PATH) -> None:
        self.csv_path = csv_path
        self._dataframe: pd.DataFrame | None = None

    def get_dataframe(self) -> pd.DataFrame:
        if self._dataframe is None:
            if not self.csv_path.exists():
                raise FileNotFoundError(f"PrimeKG 处理后 CSV 不存在：{self.csv_path}")
            self._dataframe = pd.read_csv(self.csv_path, low_memory=False)
        return self._dataframe

    @staticmethod
    def _name_mask(dataframe: pd.DataFrame, drug_en_name: str) -> pd.Series:
        normalized = drug_en_name.strip().lower()
        x_match = dataframe["x_name"].astype(str).str.strip().str.lower() == normalized
        y_match = dataframe["y_name"].astype(str).str.strip().str.lower() == normalized
        return x_match | y_match

    def filter_by_drug_name(self, drug_en_name: str) -> pd.DataFrame:
        dataframe = self.get_dataframe()
        return dataframe[self._name_mask(dataframe, drug_en_name)].copy()

    def filter_by_drug_pair(self, drug_a_en: str, drug_b_en: str) -> pd.DataFrame:
        dataframe = self.get_dataframe()
        a = drug_a_en.strip().lower()
        b = drug_b_en.strip().lower()
        forward = (
            (dataframe["x_name"].astype(str).str.strip().str.lower() == a)
            & (dataframe["y_name"].astype(str).str.strip().str.lower() == b)
        )
        backward = (
            (dataframe["x_name"].astype(str).str.strip().str.lower() == b)
            & (dataframe["y_name"].astype(str).str.strip().str.lower() == a)
        )
        return dataframe[forward | backward].copy()

    def filter_by_keep_reason(self, drug_en_name: str, keep_reason: str) -> pd.DataFrame:
        dataframe = self.filter_by_drug_name(drug_en_name)
        normalized_reason = keep_reason.strip().lower()
        mask = dataframe["keep_reason"].astype(str).str.strip().str.lower() == normalized_reason
        return dataframe[mask].copy()

