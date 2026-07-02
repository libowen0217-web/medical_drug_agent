from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from medical_drug_agent.app.graphdb.config import Neo4jConfig
from medical_drug_agent.app.graphdb.driver import Neo4jDriverManager


def main() -> int:
    try:
        config = Neo4jConfig.from_env()
    except Exception as exc:
        print(f"KG_BACKEND: invalid")
        print(f"error: {exc}")
        return 1

    print(f"KG_BACKEND: {config.kg_backend}")
    print(f"NEO4J_URI: {config.uri or '(not set)'}")
    print(f"NEO4J_DATABASE: {config.database}")

    if not config.enabled:
        print("neo4j_enabled: false")
        print("connected: false")
        return 0

    manager = Neo4jDriverManager(config)
    try:
        connected = manager.verify_connection()
        print(f"neo4j_enabled: true")
        print(f"connected: {connected}")
        driver = manager.get_driver()
        with driver.session(database=config.database) as session:
            record = session.run(
                "CALL dbms.components() YIELD versions RETURN versions[0] AS version LIMIT 1"
            ).single()
        print(f"neo4j_version: {record.get('version') if record else 'unknown'}")
        return 0
    except Exception as exc:
        print("neo4j_enabled: true")
        print("connected: false")
        print(f"error: {exc}")
        return 1
    finally:
        manager.close()


if __name__ == "__main__":
    raise SystemExit(main())
