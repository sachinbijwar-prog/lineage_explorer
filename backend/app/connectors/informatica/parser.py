import logging
import xml.etree.ElementTree as ET
from backend.app.connectors.base.models import LineageGraph, Node, Relationship, NodeTypes

logger = logging.getLogger(__name__)


class InformaticaParser:
    """
    Parses Informatica PowerMart XML export definitions into a canonical LineageGraph.
    """

    def __init__(self, default_source_system: str = "Informatica"):
        self.default_source_system = default_source_system

    def parse(self, xml_text: str) -> LineageGraph:
        """
        Parses XML text and returns a LineageGraph.
        """
        nodes: dict[str, Node] = {}
        relationships: list[Relationship] = []

        try:
            root = ET.fromstring(xml_text)
        except Exception as e:
            logger.error(f"Failed to parse Informatica XML: {e}")
            return LineageGraph()

        # The root tag is POWERMART. We search for FOLDER elements.
        for folder in root.findall(".//FOLDER"):
            # 1. Parse SOURCES -> TABLE nodes
            for src in folder.findall("SOURCE"):
                name = src.attrib.get("NAME")
                if name:
                    name_upper = name.upper()
                    nodes[name_upper] = Node(
                        id=name_upper,
                        name=name_upper,
                        type=NodeTypes.TABLE,
                        source_system=self.default_source_system
                    )

            # 2. Parse TARGETS -> TABLE nodes
            for tgt in folder.findall("TARGET"):
                name = tgt.attrib.get("NAME")
                if name:
                    name_upper = name.upper()
                    nodes[name_upper] = Node(
                        id=name_upper,
                        name=name_upper,
                        type=NodeTypes.TABLE,
                        source_system=self.default_source_system
                    )

            # 3. Parse MAPPINGS -> MAPPING nodes and relationships
            for mapping in folder.findall("MAPPING"):
                mapping_name = mapping.attrib.get("NAME")
                if not mapping_name:
                    continue
                mapping_upper = mapping_name.upper()
                nodes[mapping_upper] = Node(
                    id=mapping_upper,
                    name=mapping_upper,
                    type=NodeTypes.MAPPING,
                    source_system=self.default_source_system
                )

                # Get all INSTANCE elements inside the mapping to find sources and targets
                for instance in mapping.findall("INSTANCE"):
                    inst_type = instance.attrib.get("TYPE")
                    trans_name = instance.attrib.get("TRANSFORMATION_NAME")
                    if not trans_name:
                        continue
                    trans_upper = trans_name.upper()

                    if inst_type == "SOURCE":
                        # Ensure node exists in graph
                        if trans_upper not in nodes:
                            nodes[trans_upper] = Node(
                                id=trans_upper,
                                name=trans_upper,
                                type=NodeTypes.TABLE,
                                source_system=self.default_source_system
                            )
                        # Relationship: SOURCE -> MAPPING
                        relationships.append(
                            Relationship(
                                source=trans_upper,
                                target=mapping_upper,
                                relationship_type="FEEDS"
                            )
                        )
                    elif inst_type == "TARGET":
                        # Ensure node exists in graph
                        if trans_upper not in nodes:
                            nodes[trans_upper] = Node(
                                id=trans_upper,
                                name=trans_upper,
                                type=NodeTypes.TABLE,
                                source_system=self.default_source_system
                            )
                        # Relationship: MAPPING -> TARGET
                        relationships.append(
                            Relationship(
                                source=mapping_upper,
                                target=trans_upper,
                                relationship_type="WRITES_TO"
                            )
                        )

            # 4. Parse WORKFLOWS -> WORKFLOW nodes and relationships
            for workflow in folder.findall("WORKFLOW"):
                workflow_name = workflow.attrib.get("NAME")
                if not workflow_name:
                    continue
                workflow_upper = workflow_name.upper()
                nodes[workflow_upper] = Node(
                    id=workflow_upper,
                    name=workflow_upper,
                    type=NodeTypes.WORKFLOW,
                    source_system=self.default_source_system
                )

                # Get all SESSION elements inside the workflow
                for session in workflow.findall("SESSION"):
                    mapping_name = session.attrib.get("MAPPINGNAME")
                    if mapping_name:
                        mapping_upper = mapping_name.upper()
                        # Ensure mapping node is declared
                        if mapping_upper not in nodes:
                            nodes[mapping_upper] = Node(
                                id=mapping_upper,
                                name=mapping_upper,
                                type=NodeTypes.MAPPING,
                                source_system=self.default_source_system
                            )
                        # Relationship: WORKFLOW -> MAPPING
                        relationships.append(
                            Relationship(
                                source=workflow_upper,
                                target=mapping_upper,
                                relationship_type="EXECUTES"
                            )
                        )

        return LineageGraph(
            nodes=list(nodes.values()),
            relationships=relationships
        )
