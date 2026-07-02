from __future__ import annotations

import csv
from pathlib import Path


class SymptomRuleStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path(__file__).resolve().parent

    def load_symptom_rules(self) -> list[dict]:
        return self._load_csv(self.base_dir / "symptom_rules.csv")

    def load_red_flags(self) -> list[dict]:
        return self._load_csv(self.base_dir / "red_flags.csv")

    def load_otc_candidate_rules(self) -> list[dict]:
        return self._load_csv(self.base_dir / "otc_candidate_rules.csv")

    def _load_csv(self, path: Path) -> list[dict]:
        if not path.exists():
            raise FileNotFoundError(f"症状规则文件不存在：{path}")
        with path.open("r", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        normalized_rows: list[dict] = []
        for row in rows:
            item = {str(key): str(value or "").strip() for key, value in row.items()}
            if "keywords" in item:
                item["keywords"] = [part.strip() for part in item["keywords"].split(";") if part.strip()]
            if "candidate_drugs" in item:
                item["candidate_drugs"] = [
                    part.strip() for part in item["candidate_drugs"].split(";") if part.strip()
                ]
            normalized_rows.append(item)
        return normalized_rows

