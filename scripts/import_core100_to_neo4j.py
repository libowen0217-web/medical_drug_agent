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
from medical_drug_agent.app.graphdb.importer import import_core100_csv_to_neo4j
from medical_drug_agent.app.graphdb.schema import create_constraints_and_indexes


def main() -> int:
    parser = argparse.ArgumentParser(description="Import core100 processed CSV into Neo4j.")
    parser.add_argument("--limit", type=int, default=None, help="Only import the first N rows for testing.")
    parser.add_argument("--clear", action="store_true", help="Clear imported Entity/Drug/Disease/Effect nodes before import.")
    args = parser.parse_args()

    try:
        config = Neo4jConfig.from_env("neo4j")
    except Exception as exc:
        print(f"Neo4j 配置无效：{exc}")
        return 1

    manager = Neo4jDriverManager(config)
    try:
        manager.verify_connection()
        driver = manager.get_driver()
        create_constraints_and_indexes(driver, database=config.database)
        stats = import_core100_csv_to_neo4j(
            driver,
            database=config.database,
            limit=args.limit,
            clear_first=args.clear,
        )
    except Exception as exc:
        print(f"Neo4j 导入失败：{exc}")
        return 1
    finally:
        manager.close()

    print(f"imported_rows: {stats.imported_rows}")
    print(f"drug_count: {stats.drug_count}")
    print(f"disease_count: {stats.disease_count}")
    print(f"effect_count: {stats.effect_count}")
    print(f"entity_count: {stats.entity_count}")
    print(f"relation_count: {stats.relation_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
