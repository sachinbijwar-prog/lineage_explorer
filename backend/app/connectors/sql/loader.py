import logging
from backend.app.core.neo4j import neo4j_conn
from backend.app.connectors.base.models import LineageGraph

logger = logging.getLogger(__name__)


class Neo4jLoader:
    """
    Loads canonical LineageGraph data into Neo4j using optimized batch transactions.
    """

    def __init__(self):
        self.driver = neo4j_conn.driver

    def init_indexes(self):
        """
        Creates constraints/indexes to optimize query lookup.
        """
        queries = [
            "CREATE INDEX table_name_idx IF NOT EXISTS FOR (n:Table) ON (n.name)",
            "CREATE INDEX view_name_idx IF NOT EXISTS FOR (n:View) ON (n.name)",
            "CREATE INDEX procedure_name_idx IF NOT EXISTS FOR (n:Procedure) ON (n.name)",
            "CREATE INDEX script_name_idx IF NOT EXISTS FOR (n:Script) ON (n.name)"
        ]
        try:
            with self.driver.session() as session:
                for query in queries:
                    session.run(query)
            logger.info("Neo4j SQL Lineage indexes initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j indexes: {e}")

    def load(self, graph: LineageGraph) -> dict:
        """
        Merges nodes and relationships into the Neo4j graph using batch processing.
        """
        # Ensure indexes exist
        self.init_indexes()

        # Group nodes by label/type so we can run UNWIND queries
        nodes_by_label: dict[str, list[dict]] = {}
        for node in graph.nodes:
            label = self._get_label_from_type(node.type)
            if label not in nodes_by_label:
                nodes_by_label[label] = []
            nodes_by_label[label].append({
                "id": node.id,
                "name": node.name,
                "type": node.type.value if hasattr(node.type, "value") else str(node.type),
                "system": node.source_system
            })

        # Group edges by type
        edges_by_type: dict[str, list[dict]] = {}
        for rel in graph.relationships:
            rtype = rel.relationship_type.upper()
            clean_rtype = "".join(c for c in rtype if c.isalnum() or c == "_")
            if clean_rtype not in edges_by_type:
                edges_by_type[clean_rtype] = []
            edges_by_type[clean_rtype].append({
                "source": rel.source,
                "target": rel.target
            })

        nodes_created = 0
        relationships_created = 0

        try:
            with self.driver.session() as session:
                # 1. Batch Merge Nodes
                for label, node_list in nodes_by_label.items():
                    if not node_list:
                        continue
                    query = f"""
                    UNWIND $nodes AS n
                    MERGE (node:{label} {{name: n.name}})
                    SET node.id = n.id,
                        node.type = n.type,
                        node.system = n.system
                    """
                    session.run(query, nodes=node_list)
                    nodes_created += len(node_list)

                # 2. Batch Merge Relationships
                for rtype, edge_list in edges_by_type.items():
                    if not edge_list:
                        continue
                    # Match on name property (which is the node identifier in our queries)
                    query = f"""
                    UNWIND $edges AS e
                    MATCH (src {{name: e.source}})
                    MATCH (tgt {{name: e.target}})
                    MERGE (src)-[r:{rtype}]->(tgt)
                    """
                    session.run(query, edges=edge_list)
                    relationships_created += len(edge_list)

            logger.info(f"Successfully loaded {nodes_created} nodes and {relationships_created} relationships.")
        except Exception as e:
            logger.error(f"Failed to load graph into Neo4j: {e}")
            raise

        return {
            "nodes_created": nodes_created,
            "relationships_created": relationships_created
        }

    def _get_label_from_type(self, node_type) -> str:
        mapping = {
            "TABLE": "Table",
            "VIEW": "View",
            "PROCEDURE": "Procedure",
            "SCRIPT": "Script",
            "WORKFLOW": "Workflow",
            "JOB": "Job",
            "MAPPING": "Mapping",
            "TRANSFORMATION": "Transformation",
            "FILE": "File"
        }
        type_str = node_type.value if hasattr(node_type, "value") else str(node_type)
        return mapping.get(type_str.upper(), "Table")
