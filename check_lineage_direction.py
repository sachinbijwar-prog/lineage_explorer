import sys, os
sys.path.append(os.path.abspath("backend"))
from backend.app.services.graph_service import GraphService

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def show(result):
    print("  Nodes:", [n["data"]["id"] for n in result["nodes"]])
    print("  Edges:")
    for e in result["edges"]:
        print(f"    {e['data']['source']} --[{e['data']['relationship']}]--> {e['data']['target']}")

# Clear cache so we use the fresh queries
from backend.app.services.graph_service import _GRAPH_CACHE
_GRAPH_CACHE.clear()

section("UPSTREAM of CDS_TRADE_FACT  (expect: DIM tables + raw + sql + shell + cron)")
show(GraphService.get_upstream_lineage("CDS_TRADE_FACT", max_depth=10))

section("DOWNSTREAM of DIM_DMO_CALENDAR  (expect: all FACT tables that DEPEND ON it)")
show(GraphService.get_downstream_lineage("DIM_DMO_CALENDAR", max_depth=10))

section("DOWNSTREAM of build_cds_trade_fact.sql  (expect: CDS_TRADE_FACT)")
show(GraphService.get_downstream_lineage("build_cds_trade_fact.sql", max_depth=5))

section("UPSTREAM of DIM_DMO_CALENDAR  (expect: no execution chain, possibly empty)")
show(GraphService.get_upstream_lineage("DIM_DMO_CALENDAR", max_depth=5))
