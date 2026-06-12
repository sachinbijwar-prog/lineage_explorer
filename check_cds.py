import sys
import os
sys.path.append(os.path.abspath("backend"))

from backend.app.core.neo4j import neo4j_conn

def run():
    print("--- CDS_TRADE_FACT NODES ---")
    with neo4j_conn.driver.session() as session:
        result = session.run("MATCH (n) WHERE n.name CONTAINS 'CDS_TRADE_FACT' OR n.id CONTAINS 'CDS_TRADE_FACT' RETURN labels(n) as labels, properties(n) as props")
        for rec in result:
            print(f"Labels: {rec['labels']}, Props: {rec['props']}")

    print("\n--- CDS_TRADE_FACT RELATIONSHIPS ---")
    with neo4j_conn.driver.session() as session:
        result = session.run(
            "MATCH (src)-[r]->(tgt) WHERE src.name CONTAINS 'CDS_TRADE_FACT' OR src.id CONTAINS 'CDS_TRADE_FACT' OR tgt.name CONTAINS 'CDS_TRADE_FACT' OR tgt.id CONTAINS 'CDS_TRADE_FACT' "
            "RETURN src.id as src_id, src.name as src_name, labels(src) as src_labels, type(r) as type, tgt.id as tgt_id, tgt.name as tgt_name, labels(tgt) as tgt_labels"
        )
        for rec in result:
            print(f"({rec['src_labels']}:{rec['src_id'] or rec['src_name']}) -[{rec['type']}]-> ({rec['tgt_labels']}:{rec['tgt_id'] or rec['tgt_name']})")

if __name__ == "__main__":
    run()
