from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from medical_drug_agent.app.constants import PROCESSED_DATA_PATH


NODE_LABEL_MAP = {
    "drug": "Drug",
    "disease": "Disease",
    "effect": "Effect",
    "phenotype": "Effect",
}

RELATION_TYPE_MAP = {
    "drug_drug": "INTERACTS_WITH",
    "synergistic interaction": "INTERACTS_WITH",
    "contraindication": "CONTRAINDICATED_FOR",
    "indication": "INDICATED_FOR",
    "off-label use": "OFF_LABEL_USE",
    "side effect": "HAS_SIDE_EFFECT",
    "drug_effect": "HAS_SIDE_EFFECT",
}


@dataclass(slots=True)
class ImportStats:
    imported_rows: int = 0
    drug_count: int = 0
    disease_count: int = 0
    effect_count: int = 0
    entity_count: int = 0
    relation_count: int = 0


def _normalize_node_label(raw_type: object) -> str:
    normalized = str(raw_type or "").strip().lower()
    return NODE_LABEL_MAP.get(normalized, "Entity")


def _normalize_relation_type(row: dict) -> str:
    candidates = [
        str(row.get("display_relation", "") or "").strip().lower(),
        str(row.get("relation", "") or "").strip().lower(),
        str(row.get("keep_reason", "") or "").strip().lower(),
    ]
    for candidate in candidates:
        if candidate in RELATION_TYPE_MAP:
            return RELATION_TYPE_MAP[candidate]
    return "RELATED_TO"


def _prepare_row(row: dict) -> dict:
    x_name = str(row.get("x_name", "") or "").strip()
    y_name = str(row.get("y_name", "") or "").strip()
    x_type = str(row.get("x_type", "") or "").strip()
    y_type = str(row.get("y_type", "") or "").strip()
    return {
        "x_name": x_name,
        "x_type": x_type,
        "x_label": _normalize_node_label(x_type),
        "x_normalized_name": x_name.lower(),
        "x_source_id": str(row.get("x_id", "") or "").strip(),
        "y_name": y_name,
        "y_type": y_type,
        "y_label": _normalize_node_label(y_type),
        "y_normalized_name": y_name.lower(),
        "y_source_id": str(row.get("y_id", "") or "").strip(),
        "relation": str(row.get("relation", "") or "").strip(),
        "display_relation": str(row.get("display_relation", "") or "").strip(),
        "source": "primekg_core100_processed_csv",
        "keep_reason": str(row.get("keep_reason", "") or "").strip(),
        "matched_core_drug": str(row.get("matched_core_drug", "") or "").strip(),
        "relation_type": _normalize_relation_type(row),
    }


def clear_imported_graph(driver, database: str = "neo4j") -> None:
    with driver.session(database=database) as session:
        session.run(
            """
            MATCH (n:Entity)
            DETACH DELETE n
            """
        )


def _group_rows(prepared_rows: list[dict]) -> dict[tuple[str, str, str], list[dict]]:
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in prepared_rows:
        key = (row["x_label"], row["y_label"], row["relation_type"])
        grouped[key].append(row)
    return grouped


def _import_group(session, x_label: str, y_label: str, relation_type: str, rows: list[dict]) -> None:
    query = f"""
    UNWIND $rows AS row
    MERGE (x:Entity:{x_label} {{normalized_name: row.x_normalized_name}})
      ON CREATE SET x.name = row.x_name, x.type = row.x_type, x.source_id = row.x_source_id
      ON MATCH SET x.name = coalesce(x.name, row.x_name), x.type = coalesce(x.type, row.x_type)
    MERGE (y:Entity:{y_label} {{normalized_name: row.y_normalized_name}})
      ON CREATE SET y.name = row.y_name, y.type = row.y_type, y.source_id = row.y_source_id
      ON MATCH SET y.name = coalesce(y.name, row.y_name), y.type = coalesce(y.type, row.y_type)
    MERGE (x)-[r:{relation_type} {{
      relation: row.relation,
      display_relation: row.display_relation,
      keep_reason: row.keep_reason,
      matched_core_drug: row.matched_core_drug,
      source: row.source
    }}]->(y)
    """
    session.run(query, rows=rows)


def import_core100_csv_to_neo4j(
    driver,
    csv_path: Path = PROCESSED_DATA_PATH,
    database: str = "neo4j",
    batch_size: int = 1000,
    limit: int | None = None,
    clear_first: bool = False,
) -> ImportStats:
    if not csv_path.exists():
        raise FileNotFoundError(f"Neo4j 导入数据文件不存在：{csv_path}")

    dataframe = pd.read_csv(csv_path, low_memory=False)
    if limit is not None:
        dataframe = dataframe.head(limit)

    if clear_first:
        clear_imported_graph(driver, database=database)

    rows = [_prepare_row(row) for row in dataframe.fillna("").to_dict(orient="records")]
    imported_rows = 0

    with driver.session(database=database) as session:
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            grouped = _group_rows(batch)
            for (x_label, y_label, relation_type), group_rows in grouped.items():
                _import_group(session, x_label, y_label, relation_type, group_rows)
            imported_rows += len(batch)
            print(f"[Neo4j Import] 已导入 {imported_rows}/{len(rows)} 行", flush=True)

        drug_count = session.run("MATCH (n:Drug) RETURN count(n) AS count").single()
        disease_count = session.run("MATCH (n:Disease) RETURN count(n) AS count").single()
        effect_count = session.run("MATCH (n:Effect) RETURN count(n) AS count").single()
        entity_count = session.run("MATCH (n:Entity) RETURN count(n) AS count").single()
        relation_count = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()

    return ImportStats(
        imported_rows=imported_rows,
        drug_count=int(drug_count.get("count", 0)),
        disease_count=int(disease_count.get("count", 0)),
        effect_count=int(effect_count.get("count", 0)),
        entity_count=int(entity_count.get("count", 0)),
        relation_count=int(relation_count.get("count", 0)),
    )
