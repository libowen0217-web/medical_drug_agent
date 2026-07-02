from medical_drug_agent.app.graphdb.neo4j_repository import Neo4jDrugRepository


class FakeResult:
    def __init__(self, records):
        self.records = list(records)

    def __iter__(self):
        return iter(self.records)

    def single(self):
        return self.records[0] if self.records else None


class FakeSession:
    def __init__(self, record_map):
        self.record_map = record_map

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def run(self, query, **params):
        if "RETURN d.name AS name" in query:
            return FakeResult(self.record_map.get("find_drug", []))
        if "MATCH (x:Drug)-[r]->(y:Drug)" in query:
            return FakeResult(self.record_map.get("pair", []))
        if "MATCH (x:Drug)-[r]-(y:Drug)" in query:
            return FakeResult(self.record_map.get("drug_drug", []))
        if "MATCH (x:Drug)-[r]-(y:Disease)" in query:
            return FakeResult(self.record_map.get("drug_disease", []))
        if "MATCH (x:Drug)-[r]-(y:Effect)" in query:
            return FakeResult(self.record_map.get("drug_effect", []))
        return FakeResult([])


class FakeDriver:
    def __init__(self, record_map):
        self.record_map = record_map

    def session(self, database=None):
        return FakeSession(self.record_map)


class FakeConfig:
    database = "neo4j"


class FakeDriverManager:
    def __init__(self, record_map):
        self.config = FakeConfig()
        self.driver = FakeDriver(record_map)

    def get_driver(self):
        return self.driver


def _relation_record(x_name: str = "Ibuprofen", y_name: str = "Nifedipine"):
    return {
        "x_name": x_name,
        "x_type": "drug",
        "y_name": y_name,
        "y_type": "drug",
        "relation": "interacts",
        "display_relation": "synergistic interaction",
        "keep_reason": "drug_drug",
        "matched_core_drug": f"{x_name};{y_name}",
        "rel_props": {
            "relation": "interacts",
            "display_relation": "synergistic interaction",
            "keep_reason": "drug_drug",
            "matched_core_drug": f"{x_name};{y_name}",
        },
    }


def test_query_pair_relations_returns_drug_relation_objects() -> None:
    repository = Neo4jDrugRepository(FakeDriverManager({"pair": [_relation_record()]}))
    result = repository.query_pair_relations("Ibuprofen", "Nifedipine")
    assert len(result) == 1
    assert result[0].keep_reason == "drug_drug"
    assert result[0].x_name == "Ibuprofen"
    assert result[0].matched_core_drug == "Ibuprofen;Nifedipine"


def test_query_pair_relations_supports_bidirectional_match_records() -> None:
    repository = Neo4jDrugRepository(
        FakeDriverManager({"pair": [_relation_record("Nifedipine", "Ibuprofen")]})
    )
    result = repository.query_pair_relations("Ibuprofen", "Nifedipine")
    assert len(result) == 1
    assert {result[0].x_name, result[0].y_name} == {"Ibuprofen", "Nifedipine"}


def test_query_drug_summary_builds_query_result() -> None:
    repository = Neo4jDrugRepository(
        FakeDriverManager(
            {
                "drug_drug": [_relation_record()],
                "drug_disease": [],
                "drug_effect": [],
            }
        )
    )
    result = repository.query_drug_summary("Ibuprofen")
    assert result.normalized_drug.en_name == "Ibuprofen"
    assert result.total_count == 1


def test_find_drug_returns_dict_when_found() -> None:
    repository = Neo4jDrugRepository(
        FakeDriverManager({"find_drug": [{"name": "Ibuprofen", "normalized_name": "ibuprofen", "type": "drug"}]})
    )
    result = repository.find_drug("Ibuprofen")
    assert result is not None
    assert result["name"] == "Ibuprofen"
