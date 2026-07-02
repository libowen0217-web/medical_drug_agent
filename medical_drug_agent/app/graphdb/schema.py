from __future__ import annotations


SCHEMA_STATEMENTS = [
    """
    CREATE CONSTRAINT drug_name IF NOT EXISTS
    FOR (d:Drug) REQUIRE d.normalized_name IS UNIQUE
    """,
    """
    CREATE CONSTRAINT disease_name IF NOT EXISTS
    FOR (d:Disease) REQUIRE d.normalized_name IS UNIQUE
    """,
    """
    CREATE CONSTRAINT effect_name IF NOT EXISTS
    FOR (e:Effect) REQUIRE e.normalized_name IS UNIQUE
    """,
    """
    CREATE CONSTRAINT entity_name IF NOT EXISTS
    FOR (e:Entity) REQUIRE e.normalized_name IS UNIQUE
    """,
    """
    CREATE INDEX entity_type IF NOT EXISTS
    FOR (n:Entity) ON (n.type)
    """,
]


def create_constraints_and_indexes(driver, database: str = "neo4j") -> None:
    with driver.session(database=database) as session:
        for statement in SCHEMA_STATEMENTS:
            session.run(statement)
