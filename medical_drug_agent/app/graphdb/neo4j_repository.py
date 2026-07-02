from __future__ import annotations

from medical_drug_agent.app.graphdb.driver import Neo4jDriverManager
from medical_drug_agent.app.normalization.mapper import DrugNameMapper
from medical_drug_agent.app.schemas import DrugInfo, DrugRelation, QueryResult


class Neo4jDrugRepository:
    def __init__(
        self,
        driver_manager: Neo4jDriverManager,
        mapper: DrugNameMapper | None = None,
    ) -> None:
        self.driver_manager = driver_manager
        self.mapper = mapper or DrugNameMapper()

    def _normalize_drug(self, drug_name: str) -> DrugInfo:
        return self.mapper.normalize(drug_name)

    def find_drug(self, drug_name: str) -> dict | None:
        normalized = self._normalize_drug(drug_name)
        driver = self.driver_manager.get_driver()
        query = """
        MATCH (d:Drug {normalized_name: $drug_name})
        RETURN d.name AS name, d.normalized_name AS normalized_name, d.type AS type
        LIMIT 1
        """
        with driver.session(database=self.driver_manager.config.database) as session:
            record = session.run(query, drug_name=normalized.en_name.lower()).single()
        if not record:
            return None
        return dict(record)

    def query_drug_summary(self, drug_name: str) -> QueryResult:
        normalized = self._normalize_drug(drug_name)
        drug_drug_relations = self.query_drug_drug_relations(drug_name)
        drug_disease_relations = self.query_drug_disease_relations(drug_name)
        drug_effect_relations = self.query_drug_effect_relations(drug_name)
        return QueryResult(
            drug_name=drug_name,
            normalized_drug=normalized,
            drug_drug_relations=drug_drug_relations,
            drug_disease_relations=drug_disease_relations,
            drug_effect_relations=drug_effect_relations,
            total_count=len(drug_drug_relations) + len(drug_disease_relations) + len(drug_effect_relations),
        )

    def query_pair_relations(self, drug_a: str, drug_b: str) -> list[DrugRelation]:
        normalized_a = self._normalize_drug(drug_a)
        normalized_b = self._normalize_drug(drug_b)
        driver = self.driver_manager.get_driver()
        query = """
        MATCH (x:Drug)-[r]->(y:Drug)
        WHERE
          (x.normalized_name = $drug_a AND y.normalized_name = $drug_b)
          OR
          (x.normalized_name = $drug_b AND y.normalized_name = $drug_a)
        RETURN
          x.name AS x_name,
          x.type AS x_type,
          y.name AS y_name,
          y.type AS y_type,
          r.relation AS relation,
          r.display_relation AS display_relation,
          r.keep_reason AS keep_reason,
          r.matched_core_drug AS matched_core_drug,
          properties(r) AS rel_props
        """
        with driver.session(database=self.driver_manager.config.database) as session:
            records = session.run(
                query,
                drug_a=normalized_a.en_name.lower(),
                drug_b=normalized_b.en_name.lower(),
            )
            return [self._record_to_relation(record) for record in records]

    def query_drug_disease_relations(self, drug_name: str, limit: int = 50) -> list[DrugRelation]:
        return self._query_relations_by_target(drug_name, target_label="Disease", limit=limit)

    def query_drug_effect_relations(self, drug_name: str, limit: int = 50) -> list[DrugRelation]:
        return self._query_relations_by_target(drug_name, target_label="Effect", limit=limit)

    def query_drug_drug_relations(self, drug_name: str, limit: int = 50) -> list[DrugRelation]:
        return self._query_relations_by_target(drug_name, target_label="Drug", limit=limit)

    def _query_relations_by_target(self, drug_name: str, target_label: str, limit: int) -> list[DrugRelation]:
        normalized = self._normalize_drug(drug_name)
        driver = self.driver_manager.get_driver()
        query = f"""
        MATCH (x:Drug)-[r]-(y:{target_label})
        WHERE x.normalized_name = $drug_name OR y.normalized_name = $drug_name
        RETURN
          x.name AS x_name,
          x.type AS x_type,
          y.name AS y_name,
          y.type AS y_type,
          r.relation AS relation,
          r.display_relation AS display_relation,
          r.keep_reason AS keep_reason,
          r.matched_core_drug AS matched_core_drug,
          properties(r) AS rel_props
        LIMIT $limit
        """
        with driver.session(database=self.driver_manager.config.database) as session:
            records = session.run(query, drug_name=normalized.en_name.lower(), limit=limit)
            return [self._record_to_relation(record) for record in records]

    @staticmethod
    def _record_to_relation(record) -> DrugRelation:
        relation_dict = Neo4jDrugRepository._record_to_relation_dict(record)
        return DrugRelation(**relation_dict)

    @staticmethod
    def _record_to_relation_dict(record) -> dict:
        rel_props = dict(record.get("rel_props", {}) or {})
        source_row = {
            "x_name": record.get("x_name"),
            "x_type": record.get("x_type"),
            "y_name": record.get("y_name"),
            "y_type": record.get("y_type"),
            **rel_props,
        }
        return {
            "x_name": str(record.get("x_name", "") or ""),
            "x_type": str(record.get("x_type", "") or ""),
            "y_name": str(record.get("y_name", "") or ""),
            "y_type": str(record.get("y_type", "") or ""),
            "relation": str(record.get("relation", "") or ""),
            "display_relation": str(record.get("display_relation", "") or ""),
            "keep_reason": str(record.get("keep_reason", "") or ""),
            "matched_core_drug": str(record.get("matched_core_drug", "") or ""),
            "source_row": source_row,
        }
