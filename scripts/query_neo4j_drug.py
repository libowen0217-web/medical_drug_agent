from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from medical_drug_agent.app.graphdb.config import Neo4jConfig
from medical_drug_agent.app.graphdb.driver import Neo4jDriverManager
from medical_drug_agent.app.graphdb.neo4j_repository import Neo4jDrugRepository
from medical_drug_agent.app.serialization import to_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Query drug relations from Neo4j.")
    parser.add_argument("--drug", required=True, help="Drug name in Chinese, English, or alias.")
    parser.add_argument("--pair", help="Optional paired drug name.")
    args = parser.parse_args()

    try:
        config = Neo4jConfig.from_env("neo4j")
    except Exception as exc:
        print(f"Neo4j 配置无效：{exc}")
        return 1

    manager = Neo4jDriverManager(config)
    repository = Neo4jDrugRepository(manager)
    try:
        manager.verify_connection()
        if args.pair:
            result = repository.query_pair_relations(args.drug, args.pair)
        else:
            result = repository.query_drug_summary(args.drug)
        print(to_json(result))
        return 0
    except Exception as exc:
        print(f"Neo4j 查询失败：{exc}")
        return 1
    finally:
        manager.close()


if __name__ == "__main__":
    raise SystemExit(main())
