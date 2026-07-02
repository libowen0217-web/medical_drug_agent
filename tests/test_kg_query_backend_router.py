from medical_drug_agent.app.graphdb.config import Neo4jConfig
from medical_drug_agent.app.knowledge.knowledge_router import KnowledgeBackendRouter
from medical_drug_agent.app.schemas import DrugInfo, QueryResult


class FakeCSVEngine:
    def __init__(self) -> None:
        self.pair_calls = 0
        self.summary_calls = 0

    def query_drug_pair(self, drug_a: str, drug_b: str):
        self.pair_calls += 1
        return [{"source": "csv", "drug_a": drug_a, "drug_b": drug_b}]

    def query_drug(self, drug_name: str):
        self.summary_calls += 1
        return QueryResult(
            drug_name=drug_name,
            normalized_drug=DrugInfo(drug_name, drug_name, drug_name, [], "", ""),
            total_count=0,
        )


class FakeNeo4jRepository:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.pair_calls = 0
        self.summary_calls = 0

    def query_pair_relations(self, drug_a: str, drug_b: str):
        self.pair_calls += 1
        if self.should_fail:
            raise RuntimeError("neo4j broken")
        return [{"source": "neo4j", "drug_a": drug_a, "drug_b": drug_b}]

    def query_drug_summary(self, drug_name: str):
        self.summary_calls += 1
        if self.should_fail:
            raise RuntimeError("neo4j broken")
        return QueryResult(
            drug_name=drug_name,
            normalized_drug=DrugInfo(drug_name, drug_name, drug_name, [], "", ""),
            total_count=0,
        )


class FakeDriverManager:
    def __init__(self, connected: bool = True) -> None:
        self.connected = connected
        self.verify_calls = 0

    def verify_connection(self) -> bool:
        self.verify_calls += 1
        if not self.connected:
            raise RuntimeError("cannot connect")
        return True

    def get_server_version(self) -> str | None:
        return "5.20.0" if self.connected else None


def test_csv_backend_uses_csv_even_when_neo4j_available() -> None:
    csv_engine = FakeCSVEngine()
    neo4j_repository = FakeNeo4jRepository()
    router = KnowledgeBackendRouter(
        backend="csv",
        csv_engine=csv_engine,
        config=Neo4jConfig(
            kg_backend="csv",
            enabled=True,
            uri="bolt://127.0.0.1:7687",
            user="neo4j",
            password="x",
        ),
        driver_manager=FakeDriverManager(connected=True),
        neo4j_repository=neo4j_repository,
    )

    result = router.query_pair_relations("Ibuprofen", "Nifedipine")
    metadata = router.get_last_metadata()

    assert result[0]["source"] == "csv"
    assert csv_engine.pair_calls == 1
    assert neo4j_repository.pair_calls == 0
    assert metadata["configured_knowledge_backend"] == "csv"
    assert metadata["active_knowledge_backend"] == "csv"
    assert metadata["knowledge_backend"] == "csv"
    assert metadata["fallback_used"] is False


def test_auto_backend_prefers_neo4j_when_available() -> None:
    csv_engine = FakeCSVEngine()
    neo4j_repository = FakeNeo4jRepository()
    router = KnowledgeBackendRouter(
        backend="auto",
        csv_engine=csv_engine,
        config=Neo4jConfig(
            kg_backend="auto",
            enabled=True,
            uri="bolt://127.0.0.1:7687",
            user="neo4j",
            password="x",
        ),
        driver_manager=FakeDriverManager(connected=True),
        neo4j_repository=neo4j_repository,
    )

    result = router.query_pair_relations("Ibuprofen", "Nifedipine")
    metadata = router.get_last_metadata()

    assert result[0]["source"] == "neo4j"
    assert neo4j_repository.pair_calls == 1
    assert csv_engine.pair_calls == 0
    assert metadata["configured_knowledge_backend"] == "auto"
    assert metadata["active_knowledge_backend"] == "neo4j"
    assert metadata["knowledge_backend"] == "neo4j"
    assert metadata["fallback_used"] is False
    assert metadata["fallback_reason"] is None


def test_auto_backend_falls_back_to_csv_when_neo4j_unavailable() -> None:
    csv_engine = FakeCSVEngine()
    neo4j_repository = FakeNeo4jRepository()
    router = KnowledgeBackendRouter(
        backend="auto",
        csv_engine=csv_engine,
        config=Neo4jConfig(
            kg_backend="auto",
            enabled=True,
            uri="bolt://127.0.0.1:7687",
            user="neo4j",
            password="x",
        ),
        driver_manager=FakeDriverManager(connected=False),
        neo4j_repository=neo4j_repository,
    )

    result = router.query_pair_relations("Ibuprofen", "Nifedipine")
    metadata = router.get_last_metadata()

    assert result[0]["source"] == "csv"
    assert neo4j_repository.pair_calls == 0
    assert csv_engine.pair_calls == 1
    assert metadata["configured_knowledge_backend"] == "auto"
    assert metadata["active_knowledge_backend"] == "csv"
    assert metadata["knowledge_backend"] == "csv"
    assert metadata["fallback_used"] is True
    assert metadata["fallback_reason"]


def test_neo4j_backend_uses_neo4j_repository_when_available() -> None:
    csv_engine = FakeCSVEngine()
    neo4j_repository = FakeNeo4jRepository()
    router = KnowledgeBackendRouter(
        backend="neo4j",
        csv_engine=csv_engine,
        config=Neo4jConfig(
            kg_backend="neo4j",
            enabled=True,
            uri="bolt://127.0.0.1:7687",
            user="neo4j",
            password="x",
        ),
        driver_manager=FakeDriverManager(connected=True),
        neo4j_repository=neo4j_repository,
    )

    result = router.query_pair_relations("Ibuprofen", "Nifedipine")
    metadata = router.get_last_metadata()

    assert result[0]["source"] == "neo4j"
    assert neo4j_repository.pair_calls == 1
    assert csv_engine.pair_calls == 0
    assert metadata["configured_knowledge_backend"] == "neo4j"
    assert metadata["active_knowledge_backend"] == "neo4j"
    assert metadata["knowledge_backend"] == "neo4j"
    assert metadata["fallback_used"] is False


def test_neo4j_backend_raises_when_query_fails() -> None:
    router = KnowledgeBackendRouter(
        backend="neo4j",
        csv_engine=FakeCSVEngine(),
        config=Neo4jConfig(
            kg_backend="neo4j",
            enabled=True,
            uri="bolt://127.0.0.1:7687",
            user="neo4j",
            password="x",
        ),
        driver_manager=FakeDriverManager(connected=True),
        neo4j_repository=FakeNeo4jRepository(should_fail=True),
    )

    try:
        router.query_pair_relations("Ibuprofen", "Nifedipine")
    except RuntimeError as exc:
        assert "neo4j broken" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected neo4j mode to raise when repository query fails")


def test_backend_status_reports_neo4j_when_auto_and_connected() -> None:
    router = KnowledgeBackendRouter(
        backend="auto",
        csv_engine=FakeCSVEngine(),
        config=Neo4jConfig(
            kg_backend="auto",
            enabled=True,
            uri="bolt://127.0.0.1:7687",
            user="neo4j",
            password="x",
        ),
        driver_manager=FakeDriverManager(connected=True),
        neo4j_repository=FakeNeo4jRepository(),
    )

    status = router.get_status()

    assert status["configured_backend"] == "auto"
    assert status["active_backend"] == "neo4j"
    assert status["configured_knowledge_backend"] == "auto"
    assert status["active_knowledge_backend"] == "neo4j"
    assert status["knowledge_backend"] == "neo4j"
    assert status["neo4j_configured"] is True
    assert status["neo4j_connected"] is True
    assert status["fallback_used"] is False
    assert status["fallback_reason"] is None
    assert status["neo4j_version"] == "5.20.0"


def test_backend_status_reports_csv_when_auto_and_disconnected() -> None:
    router = KnowledgeBackendRouter(
        backend="auto",
        csv_engine=FakeCSVEngine(),
        config=Neo4jConfig(
            kg_backend="auto",
            enabled=True,
            uri="bolt://127.0.0.1:7687",
            user="neo4j",
            password="x",
        ),
        driver_manager=FakeDriverManager(connected=False),
        neo4j_repository=FakeNeo4jRepository(),
    )

    status = router.get_status()

    assert status["configured_backend"] == "auto"
    assert status["active_backend"] == "csv"
    assert status["configured_knowledge_backend"] == "auto"
    assert status["active_knowledge_backend"] == "csv"
    assert status["knowledge_backend"] == "csv"
    assert status["neo4j_configured"] is True
    assert status["neo4j_connected"] is False
    assert status["fallback_used"] is True
    assert status["fallback_reason"]
    assert status["fallback_available"] is True
