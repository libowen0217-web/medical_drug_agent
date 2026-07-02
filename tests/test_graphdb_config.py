import os
from unittest.mock import patch

from medical_drug_agent.app.graphdb.config import Neo4jConfig


def test_csv_backend_disables_neo4j() -> None:
    with patch.dict(
        os.environ,
        {
            "KG_BACKEND": "csv",
            "NEO4J_URI": "bolt://127.0.0.1:7687",
            "NEO4J_USER": "neo4j",
            "NEO4J_PASSWORD": "secret",
            "NEO4J_DATABASE": "neo4j",
        },
        clear=False,
    ):
        config = Neo4jConfig.from_env()
    assert config.kg_backend == "csv"
    assert config.enabled is False


def test_auto_backend_enables_neo4j_when_config_complete() -> None:
    with patch.dict(
        os.environ,
        {
            "KG_BACKEND": "auto",
            "NEO4J_URI": "bolt://127.0.0.1:7687",
            "NEO4J_USER": "neo4j",
            "NEO4J_PASSWORD": "secret",
            "NEO4J_DATABASE": "neo4j",
        },
        clear=False,
    ):
        config = Neo4jConfig.from_env()
    assert config.kg_backend == "auto"
    assert config.enabled is True


def test_auto_backend_falls_back_when_config_incomplete() -> None:
    with patch.dict(
        os.environ,
        {
            "KG_BACKEND": "auto",
            "NEO4J_URI": "",
            "NEO4J_USER": "",
            "NEO4J_PASSWORD": "",
            "NEO4J_DATABASE": "neo4j",
        },
        clear=False,
    ):
        config = Neo4jConfig.from_env()
    assert config.kg_backend == "auto"
    assert config.enabled is False


def test_neo4j_backend_requires_complete_config() -> None:
    with patch.dict(
        os.environ,
        {
            "KG_BACKEND": "neo4j",
            "NEO4J_URI": "",
            "NEO4J_USER": "neo4j",
            "NEO4J_PASSWORD": "",
            "NEO4J_DATABASE": "neo4j",
        },
        clear=False,
    ):
        try:
            Neo4jConfig.from_env()
        except ValueError as exc:
            assert "NEO4J_URI" in str(exc)
            assert "NEO4J_PASSWORD" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("Expected ValueError for incomplete neo4j config")
