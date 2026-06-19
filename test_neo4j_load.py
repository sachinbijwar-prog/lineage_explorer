import sys
import os

# Add current workspace to path
sys.path.append(os.path.abspath("."))

from backend.app.services.lineage_service import LineageService


def main():
    print("Testing Lineage Ingestion to Neo4j...")
    result = LineageService.ingest_sql_directory("sql_samples")
    print(f"Ingestion result: {result}")

    graph = LineageService.get_lineage_graph()
    print(f"Total nodes in graph: {len(graph['nodes'])}")
    print(f"Total edges in graph: {len(graph['edges'])}")

    # Check if newly added nodes exist
    nodes_in_graph = [n["data"]["id"] for n in graph["nodes"]]
    print(f"Is FACT_SALES in graph? {'FACT_SALES' in nodes_in_graph}")
    print(f"Is DIM_CUSTOMER in graph? {'DIM_CUSTOMER' in nodes_in_graph}")

    print("\nRetrieving upstream lineage for FACT_SALES...")
    upstream = LineageService.get_upstream("FACT_SALES")
    print(f"Upstream nodes: {[n['data']['id'] for n in upstream['nodes']]}")

    print("\nRetrieving downstream lineage for STG_CUSTOMER...")
    downstream = LineageService.get_downstream("STG_CUSTOMER")
    print(f"Downstream nodes: {[n['data']['id'] for n in downstream['nodes']]}")


if __name__ == "__main__":
    main()
