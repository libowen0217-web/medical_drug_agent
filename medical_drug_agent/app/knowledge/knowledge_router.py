from __future__ import annotations

from medical_drug_agent.app.graphdb.config import Neo4jConfig
from medical_drug_agent.app.graphdb.driver import Neo4jDriverManager
from medical_drug_agent.app.graphdb.neo4j_repository import Neo4jDrugRepository
from medical_drug_agent.app.knowledge.local_query_engine import LocalDrugQueryEngine


class KnowledgeBackendRouter:
    def __init__(
        self,
        backend: str | None = None,
        csv_engine: LocalDrugQueryEngine | None = None,
        neo4j_repository: Neo4jDrugRepository | None = None,
        driver_manager: Neo4jDriverManager | None = None,
        config: Neo4jConfig | None = None,
    ) -> None:
        self.requested_backend = str(backend or "").strip().lower() or None
        self.csv_engine = csv_engine or LocalDrugQueryEngine()
        self.config = config or Neo4jConfig.from_env(self.requested_backend)
        self.driver_manager = driver_manager or Neo4jDriverManager(self.config)
        self.neo4j_repository = neo4j_repository or Neo4jDrugRepository(self.driver_manager)
        self._last_metadata = self._metadata(
            configured_backend=self.config.kg_backend,
            active_backend="csv",
        )

    def get_backend_name(self) -> str:
        return str(self._last_metadata.get("knowledge_backend", "csv"))

    def get_last_metadata(self) -> dict:
        return dict(self._last_metadata)

    def get_status(self) -> dict:
        neo4j_configured = bool(self.config.uri and self.config.user and self.config.password)
        neo4j_connected = False
        neo4j_version = None
        fallback_reason = None

        if self.config.enabled:
            try:
                neo4j_connected = self.driver_manager.verify_connection()
                if neo4j_connected:
                    neo4j_version = self.driver_manager.get_server_version()
            except Exception:
                neo4j_connected = False

        active_backend = "csv"
        if self.config.kg_backend == "neo4j" and neo4j_connected:
            active_backend = "neo4j"
        elif self.config.kg_backend == "auto" and neo4j_connected:
            active_backend = "neo4j"
        elif self.config.kg_backend == "auto":
            fallback_reason = "Neo4j unavailable, auto fallback to CSV"
        elif self.config.kg_backend == "neo4j" and not neo4j_connected:
            fallback_reason = "Neo4j requested but not connected"

        return {
            "configured_backend": self.config.kg_backend,
            "active_backend": active_backend,
            "configured_knowledge_backend": self.config.kg_backend,
            "active_knowledge_backend": active_backend,
            "knowledge_backend": active_backend,
            "fallback_used": bool(self.config.kg_backend == "auto" and active_backend == "csv"),
            "fallback_reason": fallback_reason,
            "neo4j_configured": neo4j_configured,
            "neo4j_connected": neo4j_connected,
            "neo4j_version": neo4j_version,
            "fallback_available": True,
        }

    def query_pair_relations(self, drug_a: str, drug_b: str):
        return self._dispatch(
            neo4j_call=lambda: self.neo4j_repository.query_pair_relations(drug_a, drug_b),
            csv_call=lambda: self.csv_engine.query_drug_pair(drug_a, drug_b),
        )

    def query_drug_summary(self, drug_name: str):
        return self._dispatch(
            neo4j_call=lambda: self.neo4j_repository.query_drug_summary(drug_name),
            csv_call=lambda: self.csv_engine.query_drug(drug_name),
        )

    def _dispatch(self, neo4j_call, csv_call):
        backend = self.config.kg_backend
        if backend == "csv":
            self._last_metadata = self._metadata(configured_backend="csv", active_backend="csv")
            return csv_call()

        if not self.config.enabled:
            if backend == "neo4j":
                raise RuntimeError("Neo4j 模式已启用，但当前 Neo4j 配置不完整")
            self._last_metadata = self._metadata(
                configured_backend=backend,
                active_backend="csv",
                fallback_used=True,
                fallback_reason="Neo4j 配置不完整，自动回退 CSV",
            )
            return csv_call()

        try:
            self.driver_manager.verify_connection()
            result = neo4j_call()
            self._last_metadata = self._metadata(configured_backend=backend, active_backend="neo4j")
            return result
        except Exception as exc:
            if backend == "neo4j":
                raise
            self._last_metadata = self._metadata(
                configured_backend=backend,
                active_backend="csv",
                fallback_used=True,
                fallback_reason=f"Neo4j query failed: {exc}",
            )
            return csv_call()

    @staticmethod
    def _metadata(
        configured_backend: str,
        active_backend: str,
        fallback_used: bool = False,
        fallback_reason: str | None = None,
    ) -> dict:
        return {
            "configured_knowledge_backend": configured_backend,
            "active_knowledge_backend": active_backend,
            "knowledge_backend": active_backend,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
        }
