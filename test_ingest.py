import sys
import os

# Add current workspace to path
sys.path.append(os.path.abspath("."))

from backend.app.connectors.sql.extractor import SqlExtractor
from backend.app.connectors.sql.parser import SqlParser


def test_extraction_and_parsing():
    extractor = SqlExtractor("sql_samples")
    scripts = extractor.extract()
    print(f"Extracted {len(scripts)} scripts.")

    parser = SqlParser()
    total_nodes = set()
    total_rels = []

    for script in scripts:
        graph = parser.parse(script["content"])
        print(f"\n--- File: {script['filename']} ---")
        print(f"Nodes found: {[n.name for n in graph.nodes]}")
        print(f"Rels found: {[(r.source, r.relationship_type, r.target) for r in graph.relationships]}")

        for node in graph.nodes:
            total_nodes.add(node.name)
        for rel in graph.relationships:
            total_rels.append(rel)

    print("\n=== Ingestion Summary ===")
    print(f"Total Unique Nodes: {len(total_nodes)}")
    print(f"Total Relationships: {len(total_rels)}")


if __name__ == "__main__":
    test_extraction_and_parsing()
