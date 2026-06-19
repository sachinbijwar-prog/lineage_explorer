import logging
import sqlglot
import sqlglot.expressions as exp
from backend.app.connectors.base.models import LineageGraph, Node, Relationship, NodeTypes

logger = logging.getLogger(__name__)


class SqlParser:
    """
    Parses SQL text into a canonical LineageGraph.
    Uses sqlglot to perform AST-based parsing and relationship detection.
    """

    def __init__(self, default_source_system: str = "SQL"):
        self.default_source_system = default_source_system

    def _extract_table_name(self, node) -> str:
        """
        Unwraps aliases and schemas to find the underlying table name.
        """
        current = node
        while True:
            if isinstance(current, exp.Alias):
                current = current.this
            elif isinstance(current, exp.Schema):
                current = current.this
            else:
                break

        if hasattr(current, "name") and current.name:
            return current.name.upper()
        return current.sql(comments=False).upper()

    def parse(self, sql_text: str) -> LineageGraph:
        """
        Parses SQL statements from the provided text and builds a LineageGraph.
        """
        nodes: dict[str, Node] = {}
        relationships: list[Relationship] = []

        try:
            statements = sqlglot.parse(sql_text)
        except Exception as e:
            logger.error(f"Failed to parse SQL text: {e}")
            return LineageGraph()

        for expression in statements:
            if not expression:
                continue

            # 1. Detect CREATE VIEW
            if isinstance(expression, exp.Create) and expression.args.get("kind") == "VIEW":
                target_name = self._extract_table_name(expression.this)

                nodes[target_name] = Node(
                    id=target_name,
                    name=target_name,
                    type=NodeTypes.VIEW,
                    source_system=self.default_source_system
                )

                select_expr = expression.expression
                if select_expr:
                    sources = self._extract_sources(select_expr)
                    for src in sources:
                        if src not in nodes:
                            nodes[src] = Node(
                                id=src,
                                name=src,
                                type=NodeTypes.TABLE,
                                source_system=self.default_source_system
                            )
                        relationships.append(
                            Relationship(
                                source=src,
                                target=target_name,
                                relationship_type="FEEDS"
                            )
                        )

            # 2. Detect CREATE TABLE AS SELECT
            elif isinstance(expression, exp.Create) and expression.args.get("kind") == "TABLE":
                target_name = self._extract_table_name(expression.this)

                nodes[target_name] = Node(
                    id=target_name,
                    name=target_name,
                    type=NodeTypes.TABLE,
                    source_system=self.default_source_system
                )

                select_expr = expression.expression
                if select_expr:
                    sources = self._extract_sources(select_expr)
                    for src in sources:
                        if src not in nodes:
                            nodes[src] = Node(
                                id=src,
                                name=src,
                                type=NodeTypes.TABLE,
                                source_system=self.default_source_system
                            )
                        relationships.append(
                            Relationship(
                                source=target_name,
                                target=src,
                                relationship_type="DEPENDS_ON"
                            )
                        )

            # 3. Detect INSERT INTO
            elif isinstance(expression, exp.Insert):
                target_name = self._extract_table_name(expression.this)

                nodes[target_name] = Node(
                    id=target_name,
                    name=target_name,
                    type=NodeTypes.TABLE,
                    source_system=self.default_source_system
                )

                select_expr = expression.expression
                if select_expr:
                    sources = self._extract_sources(select_expr)
                    for src in sources:
                        if src not in nodes:
                            nodes[src] = Node(
                                id=src,
                                name=src,
                                type=NodeTypes.TABLE,
                                source_system=self.default_source_system
                            )
                        relationships.append(
                            Relationship(
                                source=src,
                                target=target_name,
                                relationship_type="POPULATES"
                            )
                        )

            # 4. Detect MERGE INTO
            elif isinstance(expression, exp.Merge):
                target_name = self._extract_table_name(expression.this)

                nodes[target_name] = Node(
                    id=target_name,
                    name=target_name,
                    type=NodeTypes.TABLE,
                    source_system=self.default_source_system
                )

                using_expr = expression.args.get("using")
                if using_expr:
                    sources = self._extract_sources(using_expr)
                    for src in sources:
                        if src not in nodes:
                            nodes[src] = Node(
                                id=src,
                                name=src,
                                type=NodeTypes.TABLE,
                                source_system=self.default_source_system
                            )
                        relationships.append(
                            Relationship(
                                source=src,
                                target=target_name,
                                relationship_type="POPULATES"
                            )
                        )

        return LineageGraph(
            nodes=list(nodes.values()),
            relationships=relationships
        )

    def _extract_sources(self, expression) -> set[str]:
        """
        Extract physical source tables, excluding CTE aliases.
        """
        cte_names = set()
        for cte in expression.find_all(exp.CTE):
            if cte.alias:
                cte_names.add(cte.alias.upper())

        sources = set()
        for table in expression.find_all(exp.Table):
            if table.name:
                table_name = table.name.upper()
                if table_name not in cte_names:
                    sources.add(table_name)

        return sources

