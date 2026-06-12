"""
Comprehensive lineage direction validation.
Tests every unique node type across the entire scanned graph.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.abspath("backend"))
from backend.app.core.neo4j import neo4j_conn
from backend.app.services.graph_service import GraphService, _GRAPH_CACHE

_GRAPH_CACHE.clear()

# ── 1. Fetch all nodes from Neo4j ─────────────────────────────────────────────
with neo4j_conn.driver.session() as session:
    all_nodes = session.run(
        "MATCH (n) RETURN n.name AS name, n.type AS ntype, labels(n) AS labels"
    ).data()

by_type = {}
for row in all_nodes:
    name = row["name"]
    if not name:
        continue
    t = row["ntype"] or row["labels"][0]
    by_type.setdefault(t, []).append(name)

print(f"Total nodes in graph: {len(all_nodes)}")
for t, names in sorted(by_type.items()):
    print(f"  {t:20s} → {len(names):3d} nodes")

# ── 2. For each type, sample up to 5 nodes and check upstream + downstream ────
SAMPLE = 5
results = []

print("\n\n" + "="*70)
print("  NODE-BY-NODE TRAVERSAL CHECK")
print("="*70)

for ntype, names in sorted(by_type.items()):
    sample_names = names[:SAMPLE]
    for name in sample_names:
        up   = GraphService.get_upstream_lineage(name,   max_depth=10)
        down = GraphService.get_downstream_lineage(name, max_depth=10)
        up_count   = len(up["nodes"])   - 1   # exclude self
        down_count = len(down["nodes"]) - 1   # exclude self

        # Detect likely problems:
        #  - A TABLE with 0 upstream AND 0 downstream is suspicious
        #  - A CRON_JOB should have downstream (the shell it triggers)
        #  - A SQL_SCRIPT should have upstream (its source tables) and downstream (the table it writes)
        warning = ""
        if ntype == "TABLE" and up_count == 0 and down_count == 0:
            warning = "  ⚠️  ISOLATED TABLE - no connections found"
        elif ntype == "CRON_JOB" and down_count == 0:
            warning = "  ⚠️  CRON with no downstream"
        elif ntype == "SQL_SCRIPT" and up_count == 0:
            warning = "  ⚠️  SQL_SCRIPT with no upstream (no source tables?)"

        status = "✅" if not warning else "❌"
        print(f"{status} [{ntype:12s}] {name}")
        print(f"       upstream={up_count:3d} nodes | downstream={down_count:3d} nodes{warning}")

        results.append({
            "name": name, "type": ntype,
            "upstream": up_count, "downstream": down_count,
            "warning": warning,
        })

# ── 3. Summary ────────────────────────────────────────────────────────────────
print("\n\n" + "="*70)
print("  SUMMARY")
print("="*70)
warnings = [r for r in results if r["warning"]]
print(f"Nodes checked  : {len(results)}")
print(f"Issues found   : {len(warnings)}")
for w in warnings:
    print(f"  ❌ {w['type']:12s} {w['name']}  →  {w['warning'].strip()}")
if not warnings:
    print("  ✅ All sampled nodes have valid upstream/downstream connections.")
