from __future__ import annotations

from typing import Any

from medical_drug_agent.app.graphdb.config import Neo4jConfig

try:  # pragma: no cover - import availability depends on environment
    from neo4j import GraphDatabase
except ImportError:  # pragma: no cover
    GraphDatabase = None


class Neo4jDriverManager:
    def __init__(self, config: Neo4jConfig) -> None:
        self.config = config
        self._driver: Any | None = None

    def get_driver(self):
        if not self.config.enabled:
            raise RuntimeError("Neo4j 未启用，无法创建驱动连接")
        if GraphDatabase is None:
            raise RuntimeError("未安装 neo4j Python driver，请先安装 requirements.txt 中的 neo4j 依赖")
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password),
            )
        return self._driver

    def verify_connection(self) -> bool:
        driver = self.get_driver()
        try:
            with driver.session(database=self.config.database) as session:
                result = session.run("RETURN 1 AS ok")
                record = result.single()
            return bool(record and record.get("ok") == 1)
        except Exception as exc:
            raise RuntimeError(
                f"Neo4j 连接验证失败：uri={self.config.uri}, database={self.config.database}, error={exc}"
            ) from exc

    def get_server_version(self) -> str | None:
        driver = self.get_driver()
        try:
            with driver.session(database=self.config.database) as session:
                record = session.run(
                    "CALL dbms.components() YIELD versions RETURN versions[0] AS version"
                ).single()
            if not record:
                return None
            version = record.get("version")
            return str(version) if version is not None else None
        except Exception:
            return None

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None
