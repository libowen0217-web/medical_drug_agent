from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medical_drug_agent.app.evidence.store import EvidenceStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search local evidence snippets by keywords.")
    parser.add_argument("--keyword", action="append", required=True, dest="keywords")
    parser.add_argument("--limit", type=int, default=5)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    results = EvidenceStore().search_by_keywords(args.keywords, limit=args.limit)
    if not results:
        print("未找到匹配证据。")
        return 0

    from medical_drug_agent.app.evidence.citation import EvidenceCitationBuilder

    ranked_results = EvidenceCitationBuilder().assign_citations(results, top_k=args.limit)
    for item in ranked_results:
        print(f"rank: {item.rank}")
        print(f"citation_label: {item.citation_label}")
        print(f"evidence_id: {item.evidence_id}")
        print(f"score: {item.score:.1f}")
        print(f"topic: {item.topic}")
        print(f"source_name: {item.source_name}")
        print(f"matched_keywords: {', '.join(item.matched_keywords)}")
        print(f"evidence_text: {item.evidence_text}")
        print(f"matched_reason: {item.matched_reason}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
