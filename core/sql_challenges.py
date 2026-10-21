"""Free-form SQL challenges plus a result-set checker.

Each challenge ships a reference query. We run the reference and the user's
query on a *fresh copy* of the sample warehouse and compare result sets:

* column count must match (column names are ignored),
* row count must match,
* row order only matters when ``Challenge.ordered`` is true.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

import pandas as pd

from core.sql_data import build_db


# --------------------------------------------------------------------------- #
#  Challenge definitions
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Challenge:
    id: str
    title: str
    difficulty: str
    prompt: str
    reference_sql: str
    tables: tuple = ()
    ordered: bool = False
    hint: str = ""


CHALLENGES = [
    Challenge(
        id="fr_customers",
        title="French customers",
        difficulty="easy",
        prompt="Return **every column** for all customers whose `country` is `'FR'`.",
        reference_sql="SELECT * FROM customers WHERE country = 'FR';",
        tables=("customers",),
        hint="A plain `WHERE` filter on `country` is enough.",
    ),
    Challenge(
        id="big_shipped_orders",
        title="Large shipped orders",
        difficulty="easy",
        prompt=(
            "Return `order_id` and `amount` for orders that are `shipped` "
            "**and** have an `amount` strictly greater than 200."
        ),
        reference_sql=(
            "SELECT order_id, amount FROM orders "
            "WHERE status = 'shipped' AND amount > 200;"
        ),
        tables=("orders",),
        hint="Combine the two conditions with `AND`.",
    ),
    Challenge(
        id="customers_per_country",
        title="Customers per country",
        difficulty="easy",
        prompt=(
            "Return one row per `country` with the number of customers, "
            "as `country, n_customers`."
        ),
        reference_sql=(
            "SELECT country, COUNT(*) AS n_customers "
            "FROM customers GROUP BY country;"
        ),
        tables=("customers",),
        hint="`GROUP BY country` plus `COUNT(*)`.",
    ),
    Challenge(
        id="customers_without_orders",
        title="Customers without orders",
        difficulty="easy",
        prompt=(
            "Return `customer_id` and `name` of customers who have never "
            "placed an order."
        ),
        reference_sql="""SELECT c.customer_id,
       c.name
FROM customers c
LEFT JOIN orders o
       ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;""",
        tables=("customers", "orders"),
        hint=(
            "Anti-join: `LEFT JOIN orders ... WHERE o.order_id IS NULL`, "
            "or a `NOT EXISTS` subquery."
        ),
    ),
    Challenge(
        id="products_never_ordered",
        title="Products never ordered",
        difficulty="medium",
        prompt=(
            "Return `product_id` and `name` of products that never appear "
            "in `order_items`."
        ),
        reference_sql="""SELECT p.product_id,
       p.name
FROM products p
LEFT JOIN order_items oi
       ON oi.product_id = p.product_id
WHERE oi.item_id IS NULL;""",
        tables=("products", "order_items"),
        hint="Same anti-join pattern, this time on `order_items.product_id`.",
    ),
    Challenge(
        id="revenue_per_customer",
        title="Shipped revenue per customer",
        difficulty="medium",
        prompt=(
            "For **every** customer return `customer_id`, `name` and "
            "`total_revenue` — the sum of their `shipped` order amounts "
            "(0 when they have none)."
        ),
        reference_sql="""SELECT c.customer_id,
       c.name,
       COALESCE(SUM(o.amount), 0) AS total_revenue
FROM customers c
LEFT JOIN orders o
       ON o.customer_id = c.customer_id
      AND o.status = 'shipped'
GROUP BY c.customer_id, c.name;""",
        tables=("customers", "orders"),
        hint=(
            "`LEFT JOIN` with the status filter in the `ON` clause — not in "
            "`WHERE`, otherwise you turn the outer join into an inner one."
        ),
    ),
    Challenge(
        id="latest_order",
        title="Latest order per customer",
        difficulty="medium",
        prompt=(
            "Return `customer_id` and `order_id` of every customer's most "
            "recent order (`order_date`), breaking ties with the higher "
            "`order_id`. Only customers with at least one order."
        ),
        reference_sql="""SELECT customer_id, order_id
FROM (
    SELECT customer_id,
           order_id,
           ROW_NUMBER() OVER (
               PARTITION BY customer_id
               ORDER BY order_date DESC, order_id DESC
           ) AS rn
    FROM orders
) t
WHERE rn = 1;""",
        tables=("orders",),
        hint=(
            "`ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)`, then keep "
            "`rn = 1` in an outer query."
        ),
    ),
    Challenge(
        id="monthly_2024",
        title="Monthly shipped revenue (2024)",
        difficulty="medium",
        prompt=(
            "Return `month` (`YYYY-MM`) and total `revenue` of shipped orders "
            "per month for 2024. Only months that have at least one shipped "
            "order."
        ),
        reference_sql="""SELECT strftime('%Y-%m', order_date) AS month,
       SUM(amount) AS revenue
FROM orders
WHERE status = 'shipped'
  AND order_date >= '2024-01-01'
  AND order_date <  '2025-01-01'
GROUP BY month;""",
        tables=("orders",),
        hint=(
            "SQLite has `strftime('%Y-%m', date_column)`. Filter 2024 with a "
            "half-open range."
        ),
    ),
    Challenge(
        id="top5_orders",
        title="Top 5 orders by amount",
        difficulty="medium",
        prompt=(
            "Return `order_id` and `amount` of the five largest orders (any "
            "status), highest amount first; break ties by the lower "
            "`order_id`. **Row order matters.**"
        ),
        reference_sql="""SELECT order_id, amount
FROM orders
ORDER BY amount DESC, order_id ASC
LIMIT 5;""",
        tables=("orders",),
        ordered=True,
        hint="`ORDER BY amount DESC, order_id ASC LIMIT 5`.",
    ),
    Challenge(
        id="running_total",
        title="Running total per customer",
        difficulty="hard",
        prompt=(
            "For shipped orders only, return `customer_id, order_date, "
            "order_id, amount, running_total`, where `running_total` is the "
            "cumulative shipped amount per customer ordered by `order_date` "
            "then `order_id`. The output must be sorted by `customer_id, "
            "order_date, order_id`. **Row order matters.**"
        ),
        reference_sql="""SELECT customer_id,
       order_date,
       order_id,
       amount,
       SUM(amount) OVER (
           PARTITION BY customer_id
           ORDER BY order_date, order_id
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS running_total
FROM orders
WHERE status = 'shipped'
ORDER BY customer_id, order_date, order_id;""",
        tables=("orders",),
        ordered=True,
        hint="A window `SUM(...) OVER (PARTITION BY ... ORDER BY ...)`.",
    ),
    Challenge(
        id="manager_names",
        title="Employees and their managers",
        difficulty="hard",
        prompt=(
            "Return `employee_id`, `name` and `manager_name` for every "
            "employee; `manager_name` is `NULL` for employees without a "
            "manager."
        ),
        reference_sql="""SELECT e.employee_id,
       e.name,
       m.name AS manager_name
FROM employees e
LEFT JOIN employees m
       ON m.employee_id = e.manager_id;""",
        tables=("employees",),
        hint="Self-join `employees` to itself, aliased `e` and `m`.",
    ),
    Challenge(
        id="top_earner_per_dept",
        title="Top earner per department",
        difficulty="hard",
        prompt=(
            "Return `department`, `name` and `salary` of the highest-paid "
            "employee in each department (one row per department; break ties "
            "with the lower `employee_id`)."
        ),
        reference_sql="""SELECT department, name, salary
FROM (
    SELECT department,
           name,
           salary,
           ROW_NUMBER() OVER (
               PARTITION BY department
               ORDER BY salary DESC, employee_id ASC
           ) AS rn
    FROM employees
) t
WHERE rn = 1;""",
        tables=("employees",),
        hint="`ROW_NUMBER()` partitioned by department, keep `rn = 1`.",
    ),
    Challenge(
        id="above_average_revenue",
        title="Above-average customers",
        difficulty="hard",
        prompt=(
            "Return `customer_id, name, revenue` for customers whose total "
            "shipped revenue is **strictly greater** than the average total "
            "shipped revenue across all customers (customers with no shipped "
            "orders count as 0)."
        ),
        reference_sql="""WITH revenue AS (
    SELECT c.customer_id,
           c.name,
           COALESCE(SUM(o.amount), 0) AS revenue
    FROM customers c
    LEFT JOIN orders o
           ON o.customer_id = c.customer_id
          AND o.status = 'shipped'
    GROUP BY c.customer_id, c.name
)
SELECT customer_id, name, revenue
FROM revenue
WHERE revenue > (SELECT AVG(revenue) FROM revenue);""",
        tables=("customers", "orders"),
        hint=(
            "Build a `WITH` block with per-customer revenue, then compare it "
            "to `(SELECT AVG(revenue) FROM revenue)`."
        ),
    ),
]

_BY_ID = {c.id: c for c in CHALLENGES}


def get_challenge(challenge_id: str) -> Challenge:
    return _BY_ID[challenge_id]


# --------------------------------------------------------------------------- #
#  Safety: only a single read-only statement
# --------------------------------------------------------------------------- #
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_LINE_COMMENT = re.compile(r"--[^\n]*")
_STRING_LITERAL = re.compile(r"'(?:[^']|'')*'")
_SELECT_START = re.compile(r"^\s*(select|with)\b", re.I)
_WRITE_KEYWORD = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|vacuum|reindex)\b",
    re.I,
)


def check_read_only(sql: str) -> str | None:
    """Return an error message when `sql` is not a single read-only query."""
    body = _LINE_COMMENT.sub(" ", _BLOCK_COMMENT.sub(" ", sql)).strip()
    body = body.rstrip(";").strip()
    if not body:
        return "Write a query first."

    plain = _STRING_LITERAL.sub("''", body)  # hide keywords inside literals
    if ";" in plain:
        return "Only one SQL statement at a time, please."
    if not _SELECT_START.match(plain):
        return "Only `SELECT` / `WITH` queries are allowed here."
    if _WRITE_KEYWORD.search(plain):
        return "This page only runs read-only queries."
    return None


# --------------------------------------------------------------------------- #
#  Result checking
# --------------------------------------------------------------------------- #
@dataclass
class CheckOutcome:
    ok: bool
    reason: str  # ok | unsafe | error | columns | rows | content | order
    message: str
    user_df: pd.DataFrame | None = None
    ref_df: pd.DataFrame | None = None
    missing: list | None = None
    extra: list | None = None


def _norm(value):
    if value is None:
        return None
    if isinstance(value, float):
        if value != value:  # NaN
            return None
        return round(value, 6)
    return value


def _row_tuples(df: pd.DataFrame) -> list:
    return [tuple(_norm(v) for v in row) for row in df.itertuples(index=False, name=None)]


def _compare(user_df: pd.DataFrame, ref_df: pd.DataFrame, *, ordered: bool) -> CheckOutcome:
    if user_df.shape[1] != ref_df.shape[1]:
        return CheckOutcome(
            False,
            "columns",
            f"Expected **{ref_df.shape[1]}** column(s) but got **{user_df.shape[1]}**.",
            user_df=user_df,
            ref_df=ref_df,
        )

    user_rows = _row_tuples(user_df)
    ref_rows = _row_tuples(ref_df)

    if ordered:
        if user_rows == ref_rows:
            return CheckOutcome(True, "ok", "Correct.", user_df, ref_df)
    elif Counter(user_rows) == Counter(ref_rows):
        return CheckOutcome(True, "ok", "Correct.", user_df, ref_df)

    c_user, c_ref = Counter(user_rows), Counter(ref_rows)
    missing = list((c_ref - c_user).elements())
    extra = list((c_user - c_ref).elements())

    if not missing and not extra:
        reason = "order"
        message = "All the right rows, but not in the expected order."
    elif len(user_rows) != len(ref_rows):
        reason = "rows"
        message = (
            f"Expected **{len(ref_rows)}** row(s) but got **{len(user_rows)}**."
        )
    else:
        reason = "content"
        message = "The right number of rows, but some values differ."

    return CheckOutcome(
        False, reason, message, user_df, ref_df, missing=missing, extra=extra
    )


def evaluate(challenge: Challenge, sql: str) -> CheckOutcome:
    """Run the user's query against a fresh warehouse and compare results."""
    guard = check_read_only(sql)
    if guard:
        return CheckOutcome(False, "unsafe", guard)

    conn = build_db()
    try:
        try:
            ref_df = pd.read_sql_query(challenge.reference_sql, conn)
        except Exception as exc:  # pragma: no cover - data bug, not user error
            return CheckOutcome(False, "reference", f"Reference query failed: `{exc}`")

        try:
            user_df = pd.read_sql_query(sql, conn)
        except Exception as exc:  # noqa: BLE001
            return CheckOutcome(
                False, "error", f"Your query failed: `{exc}`", ref_df=ref_df
            )
    finally:
        conn.close()

    return _compare(user_df, ref_df, ordered=challenge.ordered)