from medical_drug_agent.app.knowledge.local_query_engine import LocalDrugQueryEngine
from medical_drug_agent.app.schemas import QueryResult


def test_query_drug_with_chinese_name_returns_query_result() -> None:
    engine = LocalDrugQueryEngine()
    result = engine.query_drug("布洛芬")
    assert isinstance(result, QueryResult)
    assert result.normalized_drug.en_name == "Ibuprofen"


def test_query_drug_with_english_name_returns_query_result() -> None:
    engine = LocalDrugQueryEngine()
    result = engine.query_drug("Ibuprofen")
    assert isinstance(result, QueryResult)
    assert result.normalized_drug.en_name == "Ibuprofen"


def test_query_drug_pair_runs_without_error() -> None:
    engine = LocalDrugQueryEngine()
    result = engine.query_drug_pair("硝苯地平", "布洛芬")
    assert isinstance(result, list)


def test_query_result_keep_reason_is_in_supported_scope() -> None:
    engine = LocalDrugQueryEngine()
    result = engine.query_drug("布洛芬")
    supported = {"drug_drug", "drug_disease", "drug_effect"}
    keep_reasons = {
        relation.keep_reason
        for relation in (
            result.drug_drug_relations
            + result.drug_disease_relations
            + result.drug_effect_relations
        )
    }
    assert keep_reasons.issubset(supported)
