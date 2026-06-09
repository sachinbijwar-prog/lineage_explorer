import time
from app.core.neo4j import neo4j_conn
from app.models.graph import UploadGraphPayload

# GPH-17: Optional Graph Caching Layer
_GRAPH_CACHE = {}
_CACHE_TTL_SECONDS = 60


class GraphService:

    @staticmethod
    def _get_cache(key: str) -> dict | None:
        entry = _GRAPH_CACHE.get(key)
        if entry and (time.time() - entry["timestamp"] < _CACHE_TTL_SECONDS):
            return entry["data"]
        return None

    @staticmethod
    def _set_cache(key: str, data: dict):
        _GRAPH_CACHE[key] = {
            "timestamp": time.time(),
            "data": data
        }

    @staticmethod
    def init_db():
        """
        GPH-16: Cypher Query Optimization
        Creates indexes on the primary lookup fields to ensure anchor node 
        matches are O(1) instead of requiring a full database scan.
        """
        queries = [
            "CREATE INDEX asset_name_idx IF NOT EXISTS FOR (n:Asset) ON (n.name)",
            "CREATE INDEX process_name_idx IF NOT EXISTS FOR (n:Process) ON (n.name)"
        ]
        with neo4j_conn.driver.session() as session:
            for q in queries:
                session.run(q)
        return True

    @staticmethod
    def upload_graph(payload: UploadGraphPayload) -> dict:
        """
        API-01: JSON Payload Ingestion API.
        Merges nodes and edges from a JSON payload into the Neo4j graph.
        """
        # 1. Categorize nodes by label based on user mapping
        asset_types = {"hive_table", "flat_file", "handshake_file", "trigger_file"}
        process_types = {"spark_job", "beeline", "shell_script"}

        assets = []
        processes = []
        unknowns = []

        for node in payload.nodes:
            n_dict = {
                "id": node.id,
                "type": node.type,
                "description": node.description,
                "owner": node.owner,
                "system": node.system
            }
            if node.type in asset_types:
                assets.append(n_dict)
            elif node.type in process_types:
                processes.append(n_dict)
            else:
                unknowns.append(n_dict)

        # 2. Group edges by relationship_type to avoid dynamic relationship Cypher errors
        edges_by_type = {}
        for edge in payload.edges:
            rtype = edge.relationship_type.upper()
            if rtype not in edges_by_type:
                edges_by_type[rtype] = []
            edges_by_type[rtype].append({"source": edge.source, "target": edge.target})

        # 3. Execute Cypher queries using UNWIND for batch performance
        with neo4j_conn.driver.session() as session:
            # Insert Assets
            if assets:
                session.run("""
                UNWIND $nodes AS n
                MERGE (node:Asset {name: n.id})
                SET node.type = n.type,
                    node.description = n.description,
                    node.owner = n.owner,
                    node.system = n.system
                """, nodes=assets)
            
            # Insert Processes
            if processes:
                session.run("""
                UNWIND $nodes AS n
                MERGE (node:Process {name: n.id})
                SET node.type = n.type,
                    node.description = n.description,
                    node.owner = n.owner,
                    node.system = n.system
                """, nodes=processes)

            # Insert Unknowns (fallback to generic Entity label)
            if unknowns:
                session.run("""
                UNWIND $nodes AS n
                MERGE (node:Entity {name: n.id})
                SET node.type = n.type,
                    node.description = n.description,
                    node.owner = n.owner,
                    node.system = n.system
                """, nodes=unknowns)

            # Insert Edges
            for rtype, edge_list in edges_by_type.items():
                # Cypher injection is safe here because rtype comes from a grouped key
                # and we can sanitize it if strictly necessary, but it's just the dict key.
                # However, to be ultra safe, ensure rtype is alphanumeric/underscore.
                clean_rtype = "".join(c for c in rtype if c.isalnum() or c == "_")
                if clean_rtype:
                    query = f"""
                    UNWIND $edges AS e
                    MATCH (src {{name: e.source}})
                    MATCH (tgt {{name: e.target}})
                    MERGE (src)-[:{clean_rtype}]->(tgt)
                    """
                    session.run(query, edges=edge_list)
        
        return {
            "status": "success",
            "nodes_inserted": len(payload.nodes),
            "edges_inserted": len(payload.edges)
        }

    @staticmethod
    def validate_graph() -> dict:
        """
        GPH-18: Graph Validation Layer
        Detects anomalies in the graph such as orphaned nodes and cyclic dependencies.
        """
        orphans_query = """
        MATCH (n)
        WHERE NOT (n)--()
        RETURN count(n) AS orphan_count
        """
        
        cycles_query = """
        MATCH path = (n)-[*]->(n)
        RETURN count(path) AS cycle_count
        """
        
        with neo4j_conn.driver.session() as session:
            orphans_result = session.run(orphans_query).single()
            cycles_result = session.run(cycles_query).single()
            
        return {
            "is_valid": cycles_result["cycle_count"] == 0,
            "orphan_count": orphans_result["orphan_count"],
            "cycle_count": cycles_result["cycle_count"]
        }

    @staticmethod
    def test_connection():
        query = """
        RETURN 'CONNECTED' AS status
        """
        with neo4j_conn.driver.session() as session:
            result = session.run(query)
            record = result.single()
            return record["status"]

    @staticmethod
    def seed_demo_graph():
        query = """
        MERGE (a:Asset {name: 'sales_orders'})
        SET a.type        = 'hive_table',
            a.description = 'Raw sales transactions from the ERP source system',
            a.owner       = 'data-engineering',
            a.system      = 'ERP'

        MERGE (p:Process {name: 'spark_sales_transform'})
        SET p.type        = 'spark_job',
            p.description = 'Aggregates raw sales orders into daily summaries',
            p.owner       = 'data-engineering',
            p.system      = 'Spark'

        MERGE (b:Asset {name: 'sales_summary'})
        SET b.type        = 'hive_table',
            b.description = 'Daily sales summary used by reporting dashboards',
            b.owner       = 'analytics',
            b.system      = 'Hive'

        MERGE (a)-[:READ_BY]->(p)
        MERGE (p)-[:WRITES_TO]->(b)
        """
        with neo4j_conn.driver.session() as session:
            session.run(query)
        return "SEEDED"

    @staticmethod
    def _map_node(neo4j_node) -> dict:
        """Map a Neo4j node object to a Cytoscape-compatible data dict."""
        return {
            "data": {
                "id":          neo4j_node["name"],
                "type":        neo4j_node.get("type", "Unknown"),
                "description": neo4j_node.get("description"),
                "owner":       neo4j_node.get("owner"),
                "system":      neo4j_node.get("system"),
            }
        }

    @staticmethod
    def _fetch_start_node(node_id: str) -> dict:
        """Fetch properties for the traversal start node from Neo4j."""
        query = "MATCH (n {name: $node_id}) RETURN n LIMIT 1"
        with neo4j_conn.driver.session() as session:
            result = session.run(query, node_id=node_id)
            record = result.single()
            if record:
                return GraphService._map_node(record["n"])
        # Fallback if node not found
        return {"data": {"id": node_id, "type": "Unknown"}}

    @staticmethod
    def get_node_details(node_id: str) -> dict | None:
        """
        API-02: Fetch metadata for a specific node directly from Neo4j.
        Returns the NodeData dictionary directly.
        """
        query = "MATCH (n {name: $node_id}) RETURN n LIMIT 1"
        with neo4j_conn.driver.session() as session:
            result = session.run(query, node_id=node_id)
            record = result.single()
            if record:
                # _map_node returns {"data": {...}}, so we unwrap it
                return GraphService._map_node(record["n"])["data"]
        return None

    @staticmethod
    def update_node_metadata(node_id: str, metadata: dict) -> dict | None:
        """
        API-03: Update specific metadata fields for a node.
        """
        set_clauses = []
        params = {"node_id": node_id}
        
        # Build dynamic SET clauses for fields that are provided
        for key, value in metadata.items():
            if value is not None:
                set_clauses.append(f"n.{key} = ${key}")
                params[key] = value
                
        if not set_clauses:
            return GraphService.get_node_details(node_id)
            
        query = f"MATCH (n {{name: $node_id}}) SET {', '.join(set_clauses)} RETURN n"
        with neo4j_conn.driver.session() as session:
            result = session.run(query, **params)
            record = result.single()
            if record:
                # Invalidate the cache whenever a node is updated to ensure lineage is fresh
                _GRAPH_CACHE.clear()
                return GraphService._map_node(record["n"])["data"]
        return None

    @staticmethod
    def get_upstream_lineage(node_id: str, max_depth: int = 10):
        cache_key = f"upstream:{node_id}:{max_depth}"
        cached = GraphService._get_cache(cache_key)
        if cached:
            return cached

        nodes = [GraphService._fetch_start_node(node_id)]
        edges = []
        seen_nodes = {node_id}
        seen_edges = set()

        # max_depth must be injected as a literal integer — Cypher does not allow
        # parameters inside variable-length path bounds (*1..N).
        upstream_query = f"""
        MATCH path = (ancestor)-[:READ_BY|WRITES_TO|DEPENDS_ON|TRIGGER_BY*1..{max_depth}]->(start {{name: $node_id}})
        RETURN nodes(path) AS path_nodes, relationships(path) AS path_rels
        """

        # Result must be consumed INSIDE the session block — session closes on exit.
        with neo4j_conn.driver.session() as session:
            result = session.run(upstream_query, node_id=node_id)

            for record in result:
                path_nodes = record["path_nodes"]
                path_rels = record["path_rels"]

                for node in path_nodes:
                    node_name = node["name"]
                    if node_name not in seen_nodes:
                        nodes.append(GraphService._map_node(node))
                        seen_nodes.add(node_name)

                for i, rel in enumerate(path_rels):
                    if i + 1 < len(path_nodes):
                        src = path_nodes[i]["name"]
                        tgt = path_nodes[i + 1]["name"]
                        rel_type = rel.type
                        edge_key = (src, tgt, rel_type)
                        if edge_key not in seen_edges:
                            edges.append({"data": {"source": src, "target": tgt, "relationship": rel_type}})
                            seen_edges.add(edge_key)

        result_dict = {"nodes": nodes, "edges": edges}
        GraphService._set_cache(cache_key, result_dict)
        return result_dict

    @staticmethod
    def get_downstream_lineage(node_id: str, max_depth: int = 10):
        cache_key = f"downstream:{node_id}:{max_depth}"
        cached = GraphService._get_cache(cache_key)
        if cached:
            return cached

        nodes = [GraphService._fetch_start_node(node_id)]
        edges = []
        seen_nodes = {node_id}
        seen_edges = set()

        # Downstream: start node radiates outward — follow relationships forward.
        # max_depth injected as a literal integer (Cypher restriction on path bounds).
        downstream_query = f"""
        MATCH path = (start {{name: $node_id}})-[:READ_BY|WRITES_TO|DEPENDS_ON|TRIGGER_BY*1..{max_depth}]->(descendant)
        RETURN nodes(path) AS path_nodes, relationships(path) AS path_rels
        """

        # Result must be consumed INSIDE the session block — session closes on exit.
        with neo4j_conn.driver.session() as session:
            result = session.run(downstream_query, node_id=node_id)

            for record in result:
                path_nodes = record["path_nodes"]
                path_rels = record["path_rels"]

                for node in path_nodes:
                    node_name = node["name"]
                    if node_name not in seen_nodes:
                        nodes.append(GraphService._map_node(node))
                        seen_nodes.add(node_name)

                for i, rel in enumerate(path_rels):
                    if i + 1 < len(path_nodes):
                        src = path_nodes[i]["name"]
                        tgt = path_nodes[i + 1]["name"]
                        rel_type = rel.type
                        edge_key = (src, tgt, rel_type)
                        if edge_key not in seen_edges:
                            edges.append({"data": {"source": src, "target": tgt, "relationship": rel_type}})
                            seen_edges.add(edge_key)

        result_dict = {"nodes": nodes, "edges": edges}
        GraphService._set_cache(cache_key, result_dict)
        return result_dict

    @staticmethod
    def get_lineage(node_id: str, direction: str = "both", max_depth: int = 10) -> dict:
        """
        Unified lineage query.

        direction:
            "upstream"   — ancestors only
            "downstream" — descendants only
            "both"       — full lineage in both directions
        """
        if direction == "upstream":
            return GraphService.get_upstream_lineage(node_id, max_depth)

        if direction == "downstream":
            return GraphService.get_downstream_lineage(node_id, max_depth)

        # direction == "both": merge upstream and downstream, de-duplicate
        upstream   = GraphService.get_upstream_lineage(node_id, max_depth)
        downstream = GraphService.get_downstream_lineage(node_id, max_depth)

        seen_node_ids = set()
        seen_edge_keys = set()
        merged_nodes = []
        merged_edges = []

        for node in upstream["nodes"] + downstream["nodes"]:
            nid = node["data"]["id"]
            if nid not in seen_node_ids:
                merged_nodes.append(node)
                seen_node_ids.add(nid)

        for edge in upstream["edges"] + downstream["edges"]:
            key = (edge["data"]["source"], edge["data"]["target"], edge["data"]["relationship"])
            if key not in seen_edge_keys:
                merged_edges.append(edge)
                seen_edge_keys.add(key)

        return {"nodes": merged_nodes, "edges": merged_edges}

    @staticmethod
    def get_impact_analysis(node_id: str, max_depth: int = 10) -> dict:
        """
        Impact Analysis Engine.

        Given a source node, returns all downstream nodes that would be affected
        if the source node changes or fails. Enriches the response with:
            - impact_summary: affected node count and max impact depth
            - impacted flag on each affected node
            - the full edge path showing how impact propagates
        """
        cache_key = f"impact:{node_id}:{max_depth}"
        cached = GraphService._get_cache(cache_key)
        if cached:
            return cached

        # Reuse downstream traversal as the impact scope
        downstream = GraphService.get_downstream_lineage(node_id, max_depth)

        nodes = downstream["nodes"]
        edges = downstream["edges"]

        # Mark the origin node vs impacted nodes
        for node in nodes:
            if node["data"]["id"] == node_id:
                node["data"]["role"] = "origin"
            else:
                node["data"]["role"] = "impacted"

        # Calculate impact depth: longest path from origin to any impacted node
        # Build an adjacency list from edges
        adjacency: dict[str, list[str]] = {}
        for edge in edges:
            src = edge["data"]["source"]
            tgt = edge["data"]["target"]
            adjacency.setdefault(src, []).append(tgt)

        # BFS from origin to find max depth
        max_impact_depth = 0
        queue = [(node_id, 0)]
        visited = {node_id}
        while queue:
            current, depth = queue.pop(0)
            max_impact_depth = max(max_impact_depth, depth)
            for neighbor in adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

        affected_count = len(nodes) - 1  # exclude origin node itself

        result_dict = {
            "origin_node": node_id,
            "nodes": nodes,
            "edges": edges,
            "impact_summary": {
                "affected_node_count": affected_count,
                "impact_depth": max_impact_depth
            }
        }
        GraphService._set_cache(cache_key, result_dict)
        return result_dict