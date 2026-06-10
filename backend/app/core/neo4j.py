from neo4j import GraphDatabase

from backend.app.core.config import settings


class Neo4jConnection:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(
                settings.neo4j_username,
                settings.neo4j_password
            )
        )

    def close(self):
        self.driver.close()


neo4j_conn = Neo4jConnection()