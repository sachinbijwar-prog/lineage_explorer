import sys
import os
sys.path.append(os.path.abspath("backend"))

from backend.app.core.neo4j import neo4j_conn

def run():
    print("--- NODES IN DB ---")
    with neo4j_conn.driver.session() as session:
        result = session.run("MATCH (n) RETURN labels(n) as labels, keys(n) as keys, properties(n) as props, n.id as id, n.name as name LIMIT 50")
        for rec in result:
            print(f"Labels: {rec['labels']}, ID: {rec['id']}, Name: {rec['name']}, Props: {rec['props']}")

    print("\n--- RELATIONSHIPS IN DB ---")
    with neo4j_conn.driver.session() as session:
        result = session.run("MATCH (src)-[r]->(tgt) RETURN src.id as src_id, src.name as src_name, type(r) as type, tgt.id as tgt_id, tgt.name as tgt_name LIMIT 50")
        for rec in result:
            print(f"({rec['src_id'] or rec['src_name']}) -[{rec['type']}]-> ({rec['tgt_id'] or rec['tgt_name']})")

if __name__ == "__main__":
    run()
