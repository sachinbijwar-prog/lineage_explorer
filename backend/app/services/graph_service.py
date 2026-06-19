import time
from backend.app.core.neo4j import neo4j_conn
from backend.app.models.graph import UploadGraphPayload

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
        """Map a Neo4j node object to a Cytoscape-compatible data dict.
        Scanner nodes use `name` as the display label but may have a prefixed `id`
        (e.g. TABLE:CDS_TRADE_FACT). We always use `name` as the Cytoscape node ID
        so that lineage traversal (which matches on name) stays consistent.
        """
        return {
            "data": {
                "id":          neo4j_node.get("name") or neo4j_node.get("id", "Unknown"),
                "type":        neo4j_node.get("type", "Unknown"),
                "description": neo4j_node.get("description"),
                "owner":       neo4j_node.get("owner"),
                "system":      neo4j_node.get("system"),
            }
        }

    @staticmethod
    def _fetch_start_node(node_id: str) -> dict:
        """Fetch properties for the traversal start node from Neo4j.
        Matches by `name` (demo/API-ingested nodes) or `id` (scanner-loaded nodes).
        """
        query = "MATCH (n) WHERE n.name = $node_id OR n.id = $node_id RETURN n LIMIT 1"
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

        # DEPENDS_ON direction: FACT_TABLE -[DEPENDS_ON]-> DIM_TABLE
        # (the dependent points TOWARD its source).
        #
        # Upstream = "what contributes to this node?"  Two semantic layers:
        #
        # Layer 1 – Execution chain (things that PRODUCE / SCHEDULE the start node).
        #   These relationships all point INTO the start node, so traverse INCOMING.
        #   e.g. SQL_SCRIPT -[SQL_WRITES]-> TABLE
        #        SHELL      -[SHELL_EXECUTES]-> SQL_SCRIPT
        #        CRON       -[CRON_TRIGGERS]->  SHELL
        #        Also includes legacy demo-graph types: READ_BY, WRITES_TO, TRIGGER_BY
        #
        # Layer 2 – Data sources (tables / objects the start node READS FROM).
        #   The scanner stores: START_TABLE -[DEPENDS_ON]-> SOURCE_TABLE
        #   so we traverse OUTGOING DEPENDS_ON / SQL_READS to find the sources.
        max_depth = max(1, min(int(max_depth), 50))

        exec_chain_query = f"""
        MATCH (start) WHERE start.name = $node_id OR start.id = $node_id
        MATCH path = (ancestor)-[:READ_BY|WRITES_TO|SQL_WRITES|CRON_TRIGGERS|SHELL_EXECUTES|TRIGGER_BY|POPULATES|FEEDS|EXECUTES*1..{max_depth}]->(start)
        RETURN nodes(path) AS path_nodes, relationships(path) AS path_rels
        """

        data_sources_query = f"""
        MATCH (start) WHERE start.name = $node_id OR start.id = $node_id
        MATCH path = (start)-[:DEPENDS_ON|SQL_READS*1..{max_depth}]->(source)
        RETURN nodes(path) AS path_nodes, relationships(path) AS path_rels
        """

        def _collect(session, query):
            for record in session.run(query, node_id=node_id):
                path_nodes = record["path_nodes"]
                path_rels  = record["path_rels"]
                for node in path_nodes:
                    node_name = node.get("name") or node.get("id", "")
                    if node_name not in seen_nodes:
                        nodes.append(GraphService._map_node(node))
                        seen_nodes.add(node_name)
                for i, rel in enumerate(path_rels):
                    if i + 1 < len(path_nodes):
                        src = path_nodes[i].get("name") or path_nodes[i].get("id", "")
                        tgt = path_nodes[i + 1].get("name") or path_nodes[i + 1].get("id", "")
                        rel_type = rel.type
                        edge_key = (src, tgt, rel_type)
                        if edge_key not in seen_edges:
                            edges.append({"data": {"source": src, "target": tgt, "relationship": rel_type}})
                            seen_edges.add(edge_key)

        with neo4j_conn.driver.session() as session:
            _collect(session, exec_chain_query)
            _collect(session, data_sources_query)

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

        # Downstream = "what does this node impact?"  Two semantic layers:
        #
        # Layer 1 – Dependents (tables / objects that DEPEND ON the start node).
        #   The scanner stores: DEPENDENT -[DEPENDS_ON|SQL_READS]-> START_NODE
        #   so we traverse INCOMING DEPENDS_ON / SQL_READS to find all dependents.
        #   This is the critical direction for impact analysis on a DIM/source table.
        #
        # Layer 2 – Execution outputs (what the start node triggers / produces).
        #   e.g. SQL_SCRIPT -[SQL_WRITES]-> OUTPUT_TABLE
        #        CRON       -[CRON_TRIGGERS]-> SHELL
        #   These relationships originate FROM the start node, so traverse OUTGOING.
        max_depth = max(1, min(int(max_depth), 50))

        dependents_query = f"""
        MATCH (start) WHERE start.name = $node_id OR start.id = $node_id
        MATCH path = (dependent)-[:DEPENDS_ON|SQL_READS*1..{max_depth}]->(start)
        RETURN nodes(path) AS path_nodes, relationships(path) AS path_rels
        """

        exec_outputs_query = f"""
        MATCH (start) WHERE start.name = $node_id OR start.id = $node_id
        MATCH path = (start)-[:SQL_WRITES|CRON_TRIGGERS|SHELL_EXECUTES|WRITES_TO|READ_BY|TRIGGER_BY|POPULATES|FEEDS|EXECUTES*1..{max_depth}]->(output)
        RETURN nodes(path) AS path_nodes, relationships(path) AS path_rels
        """

        def _collect(session, query):
            for record in session.run(query, node_id=node_id):
                path_nodes = record["path_nodes"]
                path_rels  = record["path_rels"]
                for node in path_nodes:
                    node_name = node.get("name") or node.get("id", "")
                    if node_name not in seen_nodes:
                        nodes.append(GraphService._map_node(node))
                        seen_nodes.add(node_name)
                for i, rel in enumerate(path_rels):
                    if i + 1 < len(path_nodes):
                        src = path_nodes[i].get("name") or path_nodes[i].get("id", "")
                        tgt = path_nodes[i + 1].get("name") or path_nodes[i + 1].get("id", "")
                        rel_type = rel.type
                        edge_key = (src, tgt, rel_type)
                        if edge_key not in seen_edges:
                            edges.append({"data": {"source": src, "target": tgt, "relationship": rel_type}})
                            seen_edges.add(edge_key)

        with neo4j_conn.driver.session() as session:
            _collect(session, dependents_query)
            _collect(session, exec_outputs_query)

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
    def find_shortest_paths(source_id: str, target_id: str, max_depth: int = 10) -> list[list[str]]:
        """
        Return all shortest undirected lineage paths between source and target nodes.
        Matches by name or id.
        """
        if source_id == target_id:
            with neo4j_conn.driver.session() as session:
                res = session.run(
                    "MATCH (n) WHERE n.name = $sid OR n.id = $sid RETURN COALESCE(n.name, n.id) AS name LIMIT 1",
                    sid=source_id
                ).single()
                if res:
                    return [[res["name"]]]
            raise ValueError(f"Node '{source_id}' not found in the graph.")

        max_depth = max(1, min(int(max_depth), 50))
        query = f"""
        MATCH (source) WHERE source.name = $source_id OR source.id = $source_id
        MATCH (target) WHERE target.name = $target_id OR target.id = $target_id
        MATCH path = allShortestPaths((source)-[*1..{max_depth}]-(target))
        RETURN [node IN nodes(path) | COALESCE(node.name, node.id)] AS node_names
        """

        with neo4j_conn.driver.session() as session:
            result = session.run(
                query,
                source_id=source_id,
                target_id=target_id,
            )
            paths = [record["node_names"] for record in result]

        if not paths:
            raise ValueError(f"No path found between '{source_id}' and '{target_id}' within depth {max_depth}")

        return paths

    @staticmethod
    def search_nodes(query: str, limit: int = 20) -> list:
        """
        UI-06: Search Functionality
        Search for nodes by name, type, description, owner, or system.
        Returns a list of matching nodes with their basic info.
        """
        if not query or not query.strip():
            return []
        
        # Build a case-insensitive search query
        search_term = query.strip().lower()
        cypher_query = """
        MATCH (n)
        WHERE toLower(n.name) CONTAINS $search_term
           OR toLower(n.type) CONTAINS $search_term
           OR toLower(n.description) CONTAINS $search_term
           OR toLower(n.owner) CONTAINS $search_term
           OR toLower(n.system) CONTAINS $search_term
        RETURN n
        LIMIT $limit
        """
        
        results = []
        with neo4j_conn.driver.session() as session:
            result = session.run(cypher_query, search_term=search_term, limit=limit)
            for record in result:
                node = record["n"]
                results.append({
                    "id": node["name"],
                    "type": node.get("type", "Unknown"),
                    "description": node.get("description"),
                    "owner": node.get("owner"),
                    "system": node.get("system")
                })
        
        return results

    @staticmethod
    def get_all_nodes() -> list:
        cypher_query = """
        MATCH (n)
        RETURN n.name AS id,
               COALESCE(n.type, labels(n)[0]) AS type,
               n.description AS description,
               n.owner AS owner,
               n.system AS system
        ORDER BY n.name ASC
        """
        results = []
        with neo4j_conn.driver.session() as session:
            result = session.run(cypher_query)
            for record in result:
                results.append({
                    "id": record["id"],
                    "type": record["type"] or "Unknown",
                    "description": record.get("description"),
                    "owner": record.get("owner"),
                    "system": record.get("system")
                })
        return results

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
