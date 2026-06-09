# Architecture Decision Record (ADR)

## ADR-006: Evaluation of POC Metadata Storage - JSON vs. Neo4j

### Status
Proposed

### Context
We need to determine the storage backend for the Proof of Concept (POC) phase of the Enterprise Dependency & Lineage Explorer. Currently, there is an inconsistency between the project documentation and the existing code skeleton:
* **Documentation (`Architecture.md` & `POC_IMPLEMENTATION_SPEC.md`)**: Recommends a simple JSON-file-based metadata repository for the POC, deferring Neo4j to the post-POC production phase.
* **Code Skeleton & Docker Config (`Project_Tracker.md`, `main.py`, `graph_service.py`, `docker-compose.yml`)**: Already contains Neo4j container configuration and active Neo4j connection/seeding code, with the tracker listing Neo4j tasks under Phase 4 and ADR-003 stating Neo4j is selected as the primary database.

To resolve this alignment, we evaluate and compare two paths:
1. **JSON-only POC**
2. **Neo4j-backed POC**

---

### Comparison of Options

#### 1. JSON-only POC
* **Effort**: 
  * *Initial*: Low. Requires parsing and writing a local `metadata.json` file. No database setup or external services are needed.
  * *Traversal Logic*: High. Graph operations (such as downstream impact analysis, upstream tracing, and transitive dependencies) must be implemented manually in Python using recursion or queue-based graph search algorithms.
* **Benefits**: 
  * Zero external dependencies.
  * Extremely easy to run locally or in lightweight CI/CD without Docker.
  * The dataset can be version-controlled in Git.
* **Future Alignment**: Low. Lineage exploration is inherently graph-based. Transitioning to a production database will require throwing away the Python-based traversal logic.
* **Rework**: High. All traversal and query logic written in Python will need to be rewritten in Cypher (Neo4j's query language) for the enterprise phase.

#### 2. Neo4j-backed POC
* **Effort**:
  * *Initial*: Low to Medium. Although Neo4j introduces a dependency, the Docker configuration, connection initialization boilerplate, and a seed service are already implemented in the code skeleton.
  * *Traversal Logic*: Very Low. Graph traversal (upstream, downstream, and impact analysis) can be accomplished with simple Cypher queries (e.g., variable-length path queries: `MATCH (a)-[*]->(b)`) instead of writing complex Python traversal algorithms.
* **Benefits**:
  * Out-of-the-box graph visualization support via Cypher.
  * Allows verification of the final architecture's performance and query ergonomics early in the POC.
  * No custom Python graph traversal algorithms to write, maintain, or debug.
* **Future Alignment**: High. Directly uses the target production graph technology, ensuring that queries, schemas, and indexing strategies carry over directly.
* **Rework**: Minimal. The backend code structure, API payloads, and query logic will remain largely unchanged when transitioning from POC to production.

---

### Comparison Matrix

| Evaluation Criteria | Option 1: JSON-only POC | Option 2: Neo4j-backed POC (Recommended) |
| :--- | :--- | :--- |
| **Setup Complexity** | Very Low (No external dependencies) | Low-Medium (Requires Docker Desktop / Neo4j container) |
| **Development Effort (API & Traversal)** | High (Requires writing custom recursion/BFS algorithms in Python) | Low (Leverages native Cypher graph query syntax) |
| **Future Architecture Alignment** | Low (Needs rewrite for production) | High (Direct path to production architecture) |
| **Rework Risk** | High (Discard custom python traversal logic) | Minimal (Keep Cypher queries and schemas) |
| **Current Implementation Readiness** | Low (No JSON repo/parsing exists yet) | High (Neo4j connection and seeding boilerplate already exists) |

---

### Recommendation
We recommend proceeding with **Option 2: Neo4j-backed POC**. 

**Rationale:**
1. **Infrastructure is Already Ready**: The boilerplate for Neo4j connection is already fully written in `backend/app/core/neo4j.py` and `backend/app/services/graph_service.py`, and a `docker-compose.yml` is provided. The entry barrier is negligible.
2. **Simpler Codebase**: Writing graph traversal logic in Python (BFS/DFS for upstream/downstream and impact analysis) is error-prone and requires writing more code than writing native Neo4j Cypher queries.
3. **Zero Rework for Core Logic**: By implementing the POC using Cypher, we build the real queries that will be used in production, avoiding a costly migration step later.
