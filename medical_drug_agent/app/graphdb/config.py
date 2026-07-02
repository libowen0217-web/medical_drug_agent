from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()

SUPPORTED_KG_BACKENDS = {"csv", "neo4j", "auto"}


@dataclass(slots=True)
class Neo4jConfig:
    uri: str = ""
    user: str = ""
    password: str = ""
    database: str = "neo4j"
    enabled: bool = False
    kg_backend: str = "csv"

    @classmethod
    def from_env(cls, backend_override: str | None = None) -> "Neo4jConfig":
        kg_backend = str(backend_override or os.getenv("KG_BACKEND") or "csv").strip().lower()
        if kg_backend not in SUPPORTED_KG_BACKENDS:
            raise ValueError(f"不支持的 KG_BACKEND: {kg_backend}，仅支持 csv、neo4j、auto")

        uri = str(os.getenv("NEO4J_URI") or "").strip()
        user = str(os.getenv("NEO4J_USER") or "").strip()
        password = str(os.getenv("NEO4J_PASSWORD") or "").strip()
        database = str(os.getenv("NEO4J_DATABASE") or "neo4j").strip() or "neo4j"

        has_complete_config = all([uri, user, password])
        if kg_backend == "csv":
            return cls(uri=uri, user=user, password=password, database=database, enabled=False, kg_backend=kg_backend)

        if kg_backend == "neo4j":
            missing = [name for name, value in {
                "NEO4J_URI": uri,
                "NEO4J_USER": user,
                "NEO4J_PASSWORD": password,
            }.items() if not value]
            if missing:
                raise ValueError(f"Neo4j 模式缺少必要配置：{', '.join(missing)}")
            return cls(uri=uri, user=user, password=password, database=database, enabled=True, kg_backend=kg_backend)

        return cls(
            uri=uri,
            user=user,
            password=password,
            database=database,
            enabled=has_complete_config,
            kg_backend=kg_backend,
        )
