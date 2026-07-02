from __future__ import annotations

from medical_drug_agent.app.knowledge.csv_repository import PrimeKGCSVRepository
from medical_drug_agent.app.normalization.mapper import DrugNameMapper
from medical_drug_agent.app.schemas import DrugRelation, QueryResult


class LocalDrugQueryEngine:
    """High-level local query engine backed by drug mapping and the processed CSV."""

    def __init__(
        self,
        mapper: DrugNameMapper | None = None,
        repository: PrimeKGCSVRepository | None = None,
    ) -> None:
        self.mapper = mapper or DrugNameMapper()
        self.repository = repository or PrimeKGCSVRepository()

    @staticmethod
    def _rows_to_relations(dataframe) -> list[DrugRelation]:
        relations: list[DrugRelation] = []
        for row in dataframe.to_dict(orient="records"):
            relations.append(
                DrugRelation(
                    x_name=str(row.get("x_name", "")),
                    x_type=str(row.get("x_type", "")),
                    y_name=str(row.get("y_name", "")),
                    y_type=str(row.get("y_type", "")),
                    relation=str(row.get("relation", "")),
                    display_relation=str(row.get("display_relation", "")),
                    keep_reason=str(row.get("keep_reason", "")),
                    matched_core_drug=str(row.get("matched_core_drug", "")),
                    source_row=row,
                )
            )
        return relations

    def query_drug(self, input_name: str) -> QueryResult:
        normalized_drug = self.mapper.normalize(input_name)

        drug_drug_df = self.repository.filter_by_keep_reason(normalized_drug.en_name, "drug_drug")
        drug_disease_df = self.repository.filter_by_keep_reason(normalized_drug.en_name, "drug_disease")
        drug_effect_df = self.repository.filter_by_keep_reason(normalized_drug.en_name, "drug_effect")

        drug_drug_relations = self._rows_to_relations(drug_drug_df)
        drug_disease_relations = self._rows_to_relations(drug_disease_df)
        drug_effect_relations = self._rows_to_relations(drug_effect_df)

        return QueryResult(
            drug_name=input_name,
            normalized_drug=normalized_drug,
            drug_drug_relations=drug_drug_relations,
            drug_disease_relations=drug_disease_relations,
            drug_effect_relations=drug_effect_relations,
            total_count=(
                len(drug_drug_relations)
                + len(drug_disease_relations)
                + len(drug_effect_relations)
            ),
        )

    def query_drug_pair(self, drug_a: str, drug_b: str) -> list[DrugRelation]:
        normalized_a = self.mapper.normalize(drug_a)
        normalized_b = self.mapper.normalize(drug_b)
        dataframe = self.repository.filter_by_drug_pair(normalized_a.en_name, normalized_b.en_name)
        return self._rows_to_relations(dataframe)

