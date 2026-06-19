import logging
from backend.app.connectors.base.connector import BaseConnector
from backend.app.connectors.base.models import LineageGraph, Node, Relationship, NodeTypes

logger = logging.getLogger(__name__)


class InformaticaPlaceholderConnector(BaseConnector):
    """
    Placeholder connector demonstrating how Informatica metadata (e.g. XML mappings)
    is ingested and parsed into the canonical LineageGraph model.
    """

    def ingest(self, source_xml_path: str = None) -> LineageGraph:
        """
        Simulates parsing an Informatica XML mapping export file.
        """
        logger.info(f"Simulating Informatica ingestion from XML: {source_xml_path}")

        # Hardcoded demonstration graph resembling typical Informatica workflow elements
        nodes = [
            Node(
                id="INF_WF_LOAD_SALES",
                name="INF_WF_LOAD_SALES",
                type=NodeTypes.WORKFLOW,
                source_system="Informatica"
            ),
            Node(
                id="INF_MAPPING_STG_TO_FACT",
                name="INF_MAPPING_STG_TO_FACT",
                type=NodeTypes.MAPPING,
                source_system="Informatica"
            ),
            Node(
                id="STG_SALES_TRX",
                name="STG_SALES_TRX",
                type=NodeTypes.TABLE,
                source_system="Informatica"
            ),
            Node(
                id="FACT_SALES_FINAL",
                name="FACT_SALES_FINAL",
                type=NodeTypes.TABLE,
                source_system="Informatica"
            )
        ]

        relationships = [
            Relationship(
                source="INF_WF_LOAD_SALES",
                target="INF_MAPPING_STG_TO_FACT",
                relationship_type="EXECUTES"
            ),
            Relationship(
                source="STG_SALES_TRX",
                target="INF_MAPPING_STG_TO_FACT",
                relationship_type="FEEDS"
            ),
            Relationship(
                source="INF_MAPPING_STG_TO_FACT",
                target="FACT_SALES_FINAL",
                relationship_type="WRITES_TO"
            )
        ]

        return LineageGraph(nodes=nodes, relationships=relationships)
