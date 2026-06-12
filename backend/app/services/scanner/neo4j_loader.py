import logging

from neo4j.exceptions import Neo4jError

from backend.app.core.neo4j import neo4j_conn
from backend.app.services.scanner.models import MetadataEdge, MetadataNode

logger = logging.getLogger(__name__)


class Neo4jMetadataLoader:
    def create_nodes(self, nodes: list[MetadataNode]) -> None:
        grouped: dict[str, list[dict]] = {}
        for node in nodes:
            grouped.setdefault(node.type.value, []).append(node.model_dump(mode="json"))

        try:
            with neo4j_conn.driver.session() as session:
                for label, label_nodes in grouped.items():
                    session.run(
                        f"""
                        UNWIND $nodes AS node
                        MERGE (n:{label} {{id: node.id}})
                        SET n.name = node.name,
                            n.type = node.type,
                            n.path = node.path
                        """,
                        nodes=label_nodes,
                    )
        except Neo4jError:
            logger.exception("Failed to create metadata nodes")
            raise

    def create_relationships(self, edges: list[MetadataEdge]) -> None:
        grouped: dict[str, list[dict]] = {}
        for edge in edges:
            grouped.setdefault(edge.relationship.value, []).append(
                {
                    "source": edge.source,
                    "target": edge.target,
                }
            )

        try:
            with neo4j_conn.driver.session() as session:
                for relationship, relationship_edges in grouped.items():
                    session.run(
                        f"""
                        UNWIND $edges AS edge
                        MATCH (source {{id: edge.source}})
                        MATCH (target {{id: edge.target}})
                        MERGE (source)-[:{relationship}]->(target)
                        """,
                        edges=relationship_edges,
                    )
        except Neo4jError:
            logger.exception("Failed to create metadata relationships")
            raise

    def load(self, nodes: list[MetadataNode], edges: list[MetadataEdge]) -> None:
        self.create_nodes(nodes)
        self.create_relationships(edges)
