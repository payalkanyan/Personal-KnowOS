import spacy
from neo4j import GraphDatabase
from app.core.config import settings

# Load spaCy model (small English model for NER)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Neo4j driver
_driver = None

def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    return _driver

def extract_and_store_entities(url: str, title: str, content: str, fingerprint: str):
    """
    Extract named entities from content using spaCy and store them
    as nodes/edges in Neo4j.
    """
    # Process text with spaCy (limit to first 100k chars for performance)
    doc = nlp(content[:100000])

    # Collect unique entities
    entities = {}
    for ent in doc.ents:
        if ent.label_ in ("PERSON", "ORG", "GPE", "PRODUCT", "WORK_OF_ART", "EVENT", "LAW"):
            key = (ent.text.strip(), ent.label_)
            if key not in entities and len(ent.text.strip()) > 1:
                entities[key] = ent.label_

    if not entities:
        print(f"[Neo4j] No relevant entities found in: {title[:40]}")
        return 0

    driver = get_driver()
    with driver.session() as session:
        # Create/merge the Document node
        session.run(
            """
            MERGE (d:Document {fingerprint: $fingerprint})
            SET d.url = $url, d.title = $title
            """,
            fingerprint=fingerprint, url=url, title=title
        )

        # Create/merge Entity nodes and link them to the Document
        for (name, label), _ in entities.items():
            session.run(
                """
                MERGE (e:Entity {name: $name, type: $label})
                WITH e
                MATCH (d:Document {fingerprint: $fingerprint})
                MERGE (d)-[:MENTIONS]->(e)
                """,
                name=name, label=label, fingerprint=fingerprint
            )

    entity_count = len(entities)
    print(f"[Neo4j] Extracted {entity_count} entities from: {title[:40]}")
    return entity_count
