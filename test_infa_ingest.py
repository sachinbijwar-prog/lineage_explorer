import sys
import os

# Add current workspace to path
sys.path.append(os.path.abspath("."))

from backend.app.connectors.informatica.extractor import InformaticaExtractor
from backend.app.connectors.informatica.parser import InformaticaParser


def test_extraction_and_parsing():
    extractor = InformaticaExtractor("xml_samples")
    xmls = extractor.extract()
    print(f"Extracted {len(xmls)} Informatica XML files.")

    parser = InformaticaParser()
    total_nodes = set()
    total_rels = []

    for xml_file in xmls:
        graph = parser.parse(xml_file["content"])
        print(f"\n--- File: {xml_file['filename']} ---")
        print(f"Nodes found: {[(n.name, n.type.value if hasattr(n.type, 'value') else str(n.type)) for n in graph.nodes]}")
        print(f"Rels found: {[(r.source, r.relationship_type, r.target) for r in graph.relationships]}")

        for node in graph.nodes:
            total_nodes.add(node.name)
        for rel in graph.relationships:
            total_rels.append(rel)

    print("\n=== Ingestion Summary ===")
    print(f"Total Unique Nodes: {len(total_nodes)}")
    print(f"Total Relationships: {len(total_rels)}")
    
    # Simple assertions to verify the correctness
    assert len(total_nodes) > 0, "No nodes were parsed!"
    assert len(total_rels) > 0, "No relationships were parsed!"
    
    # Asserting specific nodes exist
    nodes_list = list(total_nodes)
    assert "STG_CUSTOMER" in nodes_list, "STG_CUSTOMER table node not found"
    assert "DIM_CUSTOMER" in nodes_list, "DIM_CUSTOMER table node not found"
    assert "M_LOAD_DIM_CUSTOMER" in nodes_list, "m_load_dim_customer mapping node not found"
    assert "WF_SALES_DAILY_LOAD" in nodes_list, "wf_sales_daily_load workflow node not found"
    
    # Asserting specific relationships exist
    rel_tuples = [(r.source, r.relationship_type, r.target) for r in total_rels]
    assert ("STG_CUSTOMER", "FEEDS", "M_LOAD_DIM_CUSTOMER") in rel_tuples, "STG_CUSTOMER FEEDS mapping relationship missing"
    assert ("M_LOAD_DIM_CUSTOMER", "WRITES_TO", "DIM_CUSTOMER") in rel_tuples, "mapping WRITES_TO DIM_CUSTOMER relationship missing"
    assert ("WF_SALES_DAILY_LOAD", "EXECUTES", "M_LOAD_DIM_CUSTOMER") in rel_tuples, "workflow EXECUTES mapping relationship missing"
    
    print("\nALL INFORMATICA PARSING TESTS PASSED!")


if __name__ == "__main__":
    test_extraction_and_parsing()
