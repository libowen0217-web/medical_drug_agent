from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


DISEASE_LIBRARY_PATH = Path(__file__).resolve().parent / "disease_library.csv"


@dataclass(slots=True)
class DiseaseLibraryEntry:
    disease_id: str
    disease_name_cn: str
    disease_name_en: str = ""
    category: str = ""
    scope: str = ""
    severity: str = ""
    typical_symptoms: list[str] = field(default_factory=list)
    required_keywords: list[str] = field(default_factory=list)
    optional_keywords: list[str] = field(default_factory=list)
    red_flag_keywords: list[str] = field(default_factory=list)
    candidate_drug_classes: list[str] = field(default_factory=list)
    candidate_drugs: list[str] = field(default_factory=list)
    advice: str = ""


class DiseaseLibrary:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DISEASE_LIBRARY_PATH
        self._entries: list[DiseaseLibraryEntry] | None = None

    def load_entries(self) -> list[DiseaseLibraryEntry]:
        if self._entries is not None:
            return self._entries

        if not self.path.exists():
            raise FileNotFoundError(f"疾病库文件不存在：{self.path}")

        with self.path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        self._entries = [self._build_entry(row) for row in rows]
        return self._entries

    @staticmethod
    def _split(value: str, separators: tuple[str, ...] = (";", "|")) -> list[str]:
        text = str(value or "").strip()
        if not text:
            return []
        for separator in separators[1:]:
            text = text.replace(separator, separators[0])
        return [part.strip() for part in text.split(separators[0]) if part.strip()]

    def _build_entry(self, row: dict[str, str]) -> DiseaseLibraryEntry:
        return DiseaseLibraryEntry(
            disease_id=str(row.get("disease_id", "") or "").strip(),
            disease_name_cn=str(row.get("disease_name_cn", "") or "").strip(),
            disease_name_en=str(row.get("disease_name_en", "") or "").strip(),
            category=str(row.get("category", "") or "").strip(),
            scope=str(row.get("scope", "") or "").strip(),
            severity=str(row.get("severity", "") or "").strip(),
            typical_symptoms=self._split(str(row.get("typical_symptoms", "") or ""), separators=(";", "|")),
            required_keywords=self._split(str(row.get("required_keywords", "") or ""), separators=("|", ";")),
            optional_keywords=self._split(str(row.get("optional_keywords", "") or ""), separators=("|", ";")),
            red_flag_keywords=self._split(str(row.get("red_flag_keywords", "") or ""), separators=("|", ";")),
            candidate_drug_classes=self._split(
                str(row.get("candidate_drug_classes", "") or ""),
                separators=(";", "|"),
            ),
            candidate_drugs=self._split(str(row.get("candidate_drugs", "") or ""), separators=(";", "|")),
            advice=str(row.get("advice", "") or "").strip(),
        )
