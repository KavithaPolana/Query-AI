
import re
import sqlglot
from sqlglot import exp


ALLOWED_TABLES = {
    "customers",
    "products",
    "orders"
}


def validate_sql(sql, question=None):
    if not sql or not sql.strip():
        raise ValueError("SQL query is empty")

    sql = sql.strip().rstrip(";")

    # 1. Parse SQL using MySQL dialect
    try:
        statements = sqlglot.parse(sql, read="mysql")
    except sqlglot.errors.ParseError as error:
        raise ValueError(f"Invalid SQL syntax: {error}")

    if len(statements) != 1 or statements[0] is None:
        raise ValueError("Only one SQL statement is allowed")

    query = statements[0]

    # 2. Only SELECT queries are allowed
    if not isinstance(query, exp.Select):
        raise ValueError("Only SELECT queries are allowed")

    # 3. Block dangerous SQL operations
    blocked_patterns = [
        r"\bINTO\s+OUTFILE\b",
        r"\bINTO\s+DUMPFILE\b",
        r"\bFOR\s+UPDATE\b",
        r"\bLOCK\s+IN\s+SHARE\s+MODE\b"
    ]

    for pattern in blocked_patterns:
        if re.search(pattern, sql, re.IGNORECASE):
            raise ValueError("This SQL operation is not allowed")

    # 4. Block dangerous functions
    for function in query.find_all(exp.Func):
        function_name = function.sql_name().upper()

        if function_name in {"SLEEP", "BENCHMARK"}:
            raise ValueError(
                f"Function {function_name} is not allowed"
            )

    # 5. Check allowed tables
    referenced_tables = {
        table.name.lower()
        for table in query.find_all(exp.Table)
    }

    for table in referenced_tables:
        if table not in ALLOWED_TABLES:
            raise ValueError(
                f"Access to table '{table}' is not allowed"
            )

    # 6. Check whether SQL answers the requested calculations
    if question:
        q = question.lower()

        # Check SUM()
        if "total" in q and any(
            word in q
            for word in ["spent", "spending", "revenue", "amount"]
        ):
            if not list(query.find_all(exp.Sum)):
                raise ValueError("Expected SUM() calculation is missing")

        # Check COUNT()
        if any(
            phrase in q
            for phrase in [
                "number of orders",
                "total number",
                "count"
            ]
        ):
            if not list(query.find_all(exp.Count)):
                raise ValueError("Expected COUNT() calculation is missing")

        # Check AVG()
        if any(
            phrase in q
            for phrase in ["average", "average order value"]
        ):
            if not list(query.find_all(exp.Avg)):
                raise ValueError("Expected AVG() calculation is missing")

        # Customer spending queries should connect customers and orders
        if (
            "customer" in q
            and "order" in q
            and "customers" in referenced_tables
            and "orders" in referenced_tables
        ):
            if not query.args.get("joins"):
                raise ValueError(
                    "Expected JOIN between customers and orders"
                )

        # 7. GROUP BY validation
        # Only require GROUP BY when:
        # - The question asks for grouped results.
        # - The OUTER SELECT contains an aggregate calculation.
        #
        # Aggregates inside WHERE subqueries do not automatically
        # mean that the outer query needs GROUP BY.

        grouped_question = any(
            phrase in q
            for phrase in [
                "for each",
                "per customer",
                "per city",
                "per category"
            ]
        )

        outer_has_aggregate = any(
            list(projection.find_all(exp.AggFunc))
            for projection in query.expressions
        )

        if grouped_question and outer_has_aggregate:
            if not query.args.get("group"):
                raise ValueError("Expected GROUP BY is missing")

    # 8. Add a maximum result limit
    if not query.args.get("limit"):
        query = query.limit(100)

    # 9. Return validated MySQL SQL
    return query.sql(dialect="mysql")
