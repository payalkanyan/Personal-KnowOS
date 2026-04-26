from neo4j import GraphDatabase
from app.core.config import settings

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    return _driver


def graph_search(query: str, top_k: int = 10) -> list:
    """
    Search the Neo4j knowledge graph for documents that mention
    entities found in the query string.
    """
    driver = get_driver()
    
    with driver.session() as session:
        # Find entities whose names appear (case-insensitive) in the query
        result = session.run(
            """
            MATCH (d:Document)-[:MENTIONS]->(e:Entity)
            WHERE toLower($query) CONTAINS toLower(e.name)
            RETURN d.title AS title, d.url AS url, d.fingerprint AS fingerprint,
                   collect(DISTINCT e.name) AS matched_entities
            ORDER BY size(collect(DISTINCT e.name)) DESC
            LIMIT $top_k
            """,
            query=query, top_k=top_k
        )
        
        hits = []
        for record in result:
            hits.append({
                "title": record["title"],
                "url": record["url"],
                "fingerprint": record["fingerprint"],
                "matched_entities": record["matched_entities"],
                "source": "graph"
            })
    
    return hits
