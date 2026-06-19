import logging
from backend.app.core.neo4j import neo4j_conn
from backend.app.connectors.sql.extractor import SqlExtractor
from backend.app.connectors.sql.parser import SqlParser
from backend.app.connectors.sql.loader import Neo4jLoader
from backend.app.connectors.base.models import LineageGraph
from backend.app.connectors.informatica.extractor import InformaticaExtractor
from backend.app.connectors.informatica.parser import InformaticaParser
from backend.app.services.graph_service import GraphService

logger = logging.getLogger(__name__)


class LineageService:
    """
    Service class coordinates lineage metadata ingestion from SQL directories
    and wraps lineage traversal queries.
    """

    @staticmethod
    def ingest_sql_directory(directory_path: str = None) -> dict:
        """
        Finds all SQL scripts in the target directory, parses them for lineage,
        and loads the aggregated graph into Neo4j.
        """
        logger.info(f"Ingesting SQL directory: {directory_path or 'default'}")
        extractor = SqlExtractor(directory_path)
        parser = SqlParser()
        loader = Neo4jLoader()

        scripts = extractor.extract()
        logger.info(f"Found {len(scripts)} SQL files to process.")

        aggregated_nodes = {}
        aggregated_relationships = []
        seen_rels = set()

        for script in scripts:
            try:
                graph = parser.parse(script["content"])
                for node in graph.nodes:
                    aggregated_nodes[node.name] = node

                for rel in graph.relationships:
                    rel_key = (rel.source, rel.target, rel.relationship_type)
                    if rel_key not in seen_rels:
                        seen_rels.add(rel_key)
                        aggregated_relationships.append(rel)
            except Exception as e:
                logger.error(f"Error parsing script {script['filename']}: {e}")

        combined_graph = LineageGraph(
            nodes=list(aggregated_nodes.values()),
            relationships=aggregated_relationships
        )

        return loader.load(combined_graph)

    @staticmethod
    def ingest_informatica_directory(directory_path: str = None) -> dict:
        """
        Finds all Informatica XML scripts in the target directory, parses them for lineage,
        and loads the aggregated graph into Neo4j.
        """
        logger.info(f"Ingesting Informatica XML directory: {directory_path or 'default'}")
        extractor = InformaticaExtractor(directory_path)
        parser = InformaticaParser()
        loader = Neo4jLoader()

        xmls = extractor.extract()
        logger.info(f"Found {len(xmls)} Informatica XML files to process.")

        aggregated_nodes = {}
        aggregated_relationships = []
        seen_rels = set()

        for xml_file in xmls:
            try:
                graph = parser.parse(xml_file["content"])
                for node in graph.nodes:
                    aggregated_nodes[node.name] = node

                for rel in graph.relationships:
                    rel_key = (rel.source, rel.target, rel.relationship_type)
                    if rel_key not in seen_rels:
                        seen_rels.add(rel_key)
                        aggregated_relationships.append(rel)
            except Exception as e:
                logger.error(f"Error parsing Informatica XML file {xml_file['filename']}: {e}")

        combined_graph = LineageGraph(
            nodes=list(aggregated_nodes.values()),
            relationships=aggregated_relationships
        )

        return loader.load(combined_graph)

    @staticmethod
    def get_lineage_graph() -> dict:
        """
        Retrieves the entire lineage graph from Neo4j in Cytoscape-compatible JSON format.
        """
        nodes = {}
        edges = []

        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, r, m
        """
        try:
            with neo4j_conn.driver.session() as session:
                result = session.run(query)
                for record in result:
                    n = record["n"]
                    r = record["r"]
                    m = record["m"]

                    if n:
                        n_name = n.get("name") or n.get("id")
                        if n_name and n_name not in nodes:
                            nodes[n_name] = GraphService._map_node(n)

                    if m:
                        m_name = m.get("name") or m.get("id")
                        if m_name and m_name not in nodes:
                            nodes[m_name] = GraphService._map_node(m)

                    if r is not None and n is not None and m is not None:
                        src = n.get("name") or n.get("id")
                        tgt = m.get("name") or m.get("id")
                        rel_type = r.type
                        edges.append({
                            "data": {
                                "source": src,
                                "target": tgt,
                                "relationship": rel_type
                            }
                        })

            # De-duplicate edges
            unique_edges = []
            seen_edges = set()
            for edge in edges:
                edge_key = (edge["data"]["source"], edge["data"]["target"], edge["data"]["relationship"])
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    unique_edges.append(edge)

            return {
                "nodes": list(nodes.values()),
                "edges": unique_edges
            }
        except Exception as e:
            logger.error(f"Error fetching complete lineage graph: {e}")
            return {"nodes": [], "edges": []}

    @staticmethod
    def get_upstream(node_name: str) -> dict:
        """
        Wraps Upstream Lineage Traversal from GraphService.
        """
        return GraphService.get_upstream_lineage(node_name)

    @staticmethod
    def get_downstream(node_name: str) -> dict:
        """
        Wraps Downstream Lineage Traversal from GraphService.
        """
        return GraphService.get_downstream_lineage(node_name)
