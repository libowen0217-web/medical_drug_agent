from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medical_drug_agent.app.knowledge.local_query_engine import LocalDrugQueryEngine
from medical_drug_agent.app.schemas import DrugRelation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query local PrimeKG CSV data by drug name.")
    parser.add_argument("--drug", help="Single drug query. Supports zh/en/alias.")
    parser.add_argument("--drug-a", help="Drug A for pair query.")
    parser.add_argument("--drug-b", help="Drug B for pair query.")
    return parser


def print_relations(title: str, relations: list[DrugRelation], limit: int = 10) -> None:
    print(f"\n{title}: {len(relations)}")
    for index, relation in enumerate(relations[:limit], start=1):
        print(
            f"{index}. {relation.x_name} ({relation.x_type}) "
            f"-[{relation.display_relation}]-> {relation.y_name} ({relation.y_type}) "
            f"[{relation.keep_reason}]"
        )


def run_single(engine: LocalDrugQueryEngine, drug_name: str) -> None:
    result = engine.query_drug(drug_name)
    normalized = result.normalized_drug
    print("药物标准化结果")
    print(f"input_name: {normalized.input_name}")
    print(f"zh_name: {normalized.zh_name}")
    print(f"en_name: {normalized.en_name}")
    print(f"aliases: {', '.join(normalized.aliases) if normalized.aliases else '-'}")
    print(f"drug_class: {normalized.drug_class}")
    print(f"notes: {normalized.notes or '-'}")
    print(f"total_count: {result.total_count}")

    print_relations("drug_drug", result.drug_drug_relations)
    print_relations("drug_disease", result.drug_disease_relations)
    print_relations("drug_effect", result.drug_effect_relations)


def run_pair(engine: LocalDrugQueryEngine, drug_a: str, drug_b: str) -> None:
    normalized_a = engine.mapper.normalize(drug_a)
    normalized_b = engine.mapper.normalize(drug_b)
    relations = engine.query_drug_pair(drug_a, drug_b)

    print("药物对标准化结果")
    print(f"drug_a: {drug_a} -> {normalized_a.en_name} ({normalized_a.zh_name})")
    print(f"drug_b: {drug_b} -> {normalized_b.en_name} ({normalized_b.zh_name})")
    print_relations("pair_relations", relations, limit=20)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.drug and not (args.drug_a and args.drug_b):
        parser.error("请提供 --drug，或同时提供 --drug-a 和 --drug-b")

    engine = LocalDrugQueryEngine()
    if args.drug:
        run_single(engine, args.drug)
    else:
        run_pair(engine, args.drug_a, args.drug_b)


if __name__ == "__main__":
    main()
