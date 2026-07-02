from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "primekg_core100_drug_dataset.csv"
DRUG_NAME_MAP_PATH = PROJECT_ROOT / "medical_drug_agent" / "app" / "normalization" / "drug_name_map.csv"
RULES_DIR = PROJECT_ROOT / "medical_drug_agent" / "app" / "rules"
PHARMACY_RULES_PATH = RULES_DIR / "pharmacy_safety_rules.csv"
DOSE_DIR = PROJECT_ROOT / "medical_drug_agent" / "app" / "dose"
DOSE_REFERENCE_PATH = DOSE_DIR / "dose_reference.csv"
EVIDENCE_DIR = PROJECT_ROOT / "medical_drug_agent" / "app" / "evidence"
EVIDENCE_STORE_PATH = EVIDENCE_DIR / "evidence_store.csv"
