from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medical_drug_agent.app.evaluation.batch_runner import BatchCaseRunner
from medical_drug_agent.app.evaluation.metrics import summarize_batch_result
from medical_drug_agent.app.serialization import to_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="批量运行药物安全案例库")
    parser.add_argument("--input", required=True, help="JSONL 案例文件路径")
    parser.add_argument("--output", help="完整批量结果输出路径")
    parser.add_argument("--enable-audit", action="store_true", help="为每条案例写入审计日志")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    case_file = Path(args.input)
    runner = BatchCaseRunner()

    try:
        result = runner.run_cases(case_file, enable_audit=args.enable_audit)
    except FileNotFoundError as exc:
        print(f"错误：{exc}")
        return 1

    summary = summarize_batch_result(result)

    print(f"案例总数：{summary['total']}")
    print(f"成功数：{summary['success_count']}")
    print(f"错误数：{summary['error_count']}")
    print("风险等级统计：")
    if summary["risk_level_counts"]:
        for level, count in summary["risk_level_counts"].items():
            print(f"  {level}: {count}")
    else:
        print("  无")
    print("错误码统计：")
    if summary["error_code_counts"]:
        for code, count in summary["error_code_counts"].items():
            print(f"  {code}: {count}")
    else:
        print("  无")
    print(
        "预期匹配率："
        f"{summary['match_rate']:.2%} "
        f"({summary['matched_expected_count']}/{summary['matched_expected_count'] + summary['mismatched_expected_count']})"
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(to_json(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"完整结果已保存：{output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
