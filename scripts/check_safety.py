from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medical_drug_agent.app.dose.checker import DoseChecker
from medical_drug_agent.app.normalization.mapper import DrugNameMapper
from medical_drug_agent.app.rules.engine import SafetyRuleEngine
from medical_drug_agent.app.schemas import DoseInput, PatientInfo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check deterministic drug safety rules and dose reference.")
    parser.add_argument("--current-drug", action="append", required=True, dest="current_drugs")
    parser.add_argument("--new-drug", required=True, dest="new_drug")
    parser.add_argument("--age", type=int)
    parser.add_argument("--disease", action="append", default=[], dest="diseases")
    parser.add_argument("--patient-factor", action="append", default=[], dest="patient_factors")
    parser.add_argument("--single-dose-mg", type=float)
    parser.add_argument("--times-per-day", type=int)
    parser.add_argument("--duration-days", type=int)
    return parser


def print_drug(label: str, drug_info) -> None:
    print(f"{label}标准化结果")
    print(f"  input_name: {drug_info.input_name}")
    print(f"  zh_name: {drug_info.zh_name}")
    print(f"  en_name: {drug_info.en_name}")
    print(f"  drug_class: {drug_info.drug_class}")


def main() -> None:
    args = build_parser().parse_args()
    mapper = DrugNameMapper()
    engine = SafetyRuleEngine()
    dose_checker = DoseChecker(mapper=mapper)

    current_drugs = mapper.normalize_many(args.current_drugs)
    new_drug = mapper.normalize(args.new_drug)
    patient = PatientInfo(
        age=args.age,
        diseases=args.diseases,
        patient_factors=args.patient_factors,
    )

    for drug in current_drugs:
        print_drug("当前药物", drug)
    print_drug("新增药物", new_drug)

    matches = engine.match_rules(current_drugs=current_drugs, new_drug=new_drug, patient=patient)
    print(f"\n命中规则数量: {len(matches)}")
    for index, match in enumerate(matches, start=1):
        print(f"{index}. rule_id: {match.rule_id}")
        print(f"   risk_level: {match.risk_level}")
        print(f"   risk: {match.risk}")
        print(f"   mechanism: {match.mechanism}")
        print(f"   recommendation: {match.recommendation}")
        print(f"   evidence_note: {match.evidence_note}")
        print(f"   matched_reason: {match.matched_reason}")

    dose_input = DoseInput(
        drug_name=args.new_drug,
        single_dose_mg=args.single_dose_mg,
        times_per_day=args.times_per_day,
        duration_days=args.duration_days,
    )
    dose_result = dose_checker.check(dose_input)
    print("\n剂量检查结果")
    print(f"  drug_name: {dose_result.drug_name}")
    print(f"  status: {dose_result.status}")
    print(f"  risk_level: {dose_result.risk_level}")
    print(f"  message: {dose_result.message}")
    if dose_result.details:
        print(f"  details: {dose_result.details}")


if __name__ == "__main__":
    main()

