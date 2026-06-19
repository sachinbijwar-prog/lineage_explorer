import sys
import os
sys.path.append(os.path.abspath("backend"))

from backend.app.core.neo4j import neo4j_conn

def run():
    print("--- INFORMATICA NODES ---")
    with neo4j_conn.driver.session() as session:
        result = session.run("""
        MATCH (n)
        WHERE labels(n)[0] IN ['Workflow', 'Mapping'] OR n.name IN ['STG_CUSTOMER', 'STG_SALES', 'DIM_CUSTOMER', 'FACT_SALES']
        RETURN labels(n) as labels, n.name as name, n.type as type, n.system as system
        """)
        for rec in result:
            print(f"Labels: {rec['labels']}, Name: {rec['name']}, Type: {rec['type']}, System: {rec['system']}")

    print("\n--- INFORMATICA RELATIONSHIPS ---")
    with neo4j_conn.driver.session() as session:
        result = session.run("""
        MATCH (src)-[r:EXECUTES|FEEDS|WRITES_TO]->(tgt)
        RETURN src.name as src_name, labels(src)[0] as src_label, type(r) as type, tgt.name as tgt_name, labels(tgt)[0] as tgt_label
        """)
        for rec in result:
            print(f"({rec['src_label']}:{rec['src_name']}) -[{rec['type']}]-> ({rec['tgt_label']}:{rec['tgt_name']})")

if __name__ == "__main__":
    run()
