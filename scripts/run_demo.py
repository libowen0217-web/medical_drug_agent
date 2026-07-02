from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medical_drug_agent.app.schemas import DoseInput
from medical_drug_agent.app.workflow import DrugSafetyWorkflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local drug safety demo workflow.")
    parser.add_argument("--current-drug", action="append", dest="current_drugs")
    parser.add_argument("--new-drug")
    parser.add_argument("--age", type=int)
    parser.add_argument("--disease", action="append", default=[], dest="diseases")
    parser.add_argument("--patient-factor", action="append", default=[], dest="patient_factors")
    parser.add_argument("--single-dose-mg", type=float)
    parser.add_argument("--times-per-day", type=int)
    parser.add_argument("--duration-days", type=int)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    current_drugs = args.current_drugs or ["硝苯地平"]
    new_drug = args.new_drug or "布洛芬"
    age = args.age if args.age is not None else 68
    diseases = args.diseases or ["高血压"]
    patient_factors = args.patient_factors or []

    dose_inputs = None
    if any(
        value is not None
        for value in (args.single_dose_mg, args.times_per_day, args.duration_days)
    ):
        dose_inputs = [
            DoseInput(
                drug_name=new_drug,
                single_dose_mg=args.single_dose_mg,
                times_per_day=args.times_per_day,
                duration_days=args.duration_days,
            )
        ]

    workflow = DrugSafetyWorkflow()
    result = workflow.run(
        current_drugs=current_drugs,
        new_drug=new_drug,
        age=age,
        diseases=diseases,
        patient_factors=patient_factors,
        dose_inputs=dose_inputs,
    )

    print("=== 药师版报告 ===")
    print(result.pharmacist_report)
    print("\n=== 患者版报告 ===")
    print(result.patient_report)
    print("\n=== Safety Warnings ===")
    if result.safety_warnings:
        for warning in result.safety_warnings:
            print(f"- {warning}")
    else:
        print("无")


if __name__ == "__main__":
    main()

