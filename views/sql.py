"""SQL training page: quiz, free-form challenges, playground, cheatsheet, schema."""

import pandas as pd
import streamlit as st

from core import data, quiz_engine, state
from core.sql_challenges import (
    CHALLENGES,
    check_read_only,
    evaluate,
    get_challenge,
)
from core.sql_data import SAMPLE_DATA, get_db, reset_db

SQL_THEME = "SQL & Data Manipulation"
SQL_PREFIX = "sql_"
DEFAULT_QUERY = "SELECT * FROM customers LIMIT 5;"


def render() -> None:
    state.init_quiz_state(prefix=SQL_PREFIX)

    with st.sidebar:
        st.header("📁 Dataset")
        uploaded = st.file_uploader(
            "Upload a questions CSV", type=["csv"], key="sql_uploader"
        )
        if (
            uploaded is not None
            and uploaded.name != st.session_state.get("df_source")
        ):
            try:
                data.set_df(data.prepare(pd.read_csv(uploaded)), uploaded.name)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not read the uploaded CSV: {exc}")

        df = st.session_state.get("df")
        if df is not None:
            st.caption(
                f"Loaded: `{st.session_state.get('df_source')}` — "
                f"{len(df)} question(s)"
            )
        else:
            st.warning("No questions loaded.")

    st.title("🗄️ SQL Training")
    st.markdown(
        "Practice SQL interview questions, **write your own queries** and get "
        "them checked against the expected result, run ad-hoc SQL against a "
        "sample warehouse, and review the patterns that come up most often."
    )

    tab_quiz, tab_write, tab_play, tab_cheat, tab_schema = st.tabs(
        [
            "🧠 Quiz",
            "✍️ Write SQL",
            "▶️ Playground",
            "📚 Cheatsheet",
            "🗂️ Schema",
        ]
    )

    with tab_quiz:
        _render_quiz_tab()
    with tab_write:
        _render_write_tab()
    with tab_play:
        _render_playground_tab()
    with tab_cheat:
        _render_cheatsheet_tab()
    with tab_schema:
        _render_schema_tab()


# --------------------------------------------------------------------------- #
#  Quiz tab (multiple choice)
# --------------------------------------------------------------------------- #
def _sql_questions(df: pd.DataFrame) -> pd.DataFrame:
    mask = (df["theme"] == SQL_THEME) | df["secondary_themes"].apply(
        lambda s: SQL_THEME in data.split_multi(s)
    )
    return df[mask]


def _render_quiz_tab() -> None:
    df = st.session_state.get("df")
    if df is None:
        st.info("Load a questions CSV on the **Quiz** page first.")
        return

    sql_df = _sql_questions(df)
    if sql_df.empty:
        st.warning(
            f"No SQL questions found in the loaded dataset. "
            f"(Expected theme: `{SQL_THEME}`.)"
        )
        return

    if not state.get_state(SQL_PREFIX, "started"):
        st.markdown(f"**{len(sql_df)} SQL questions available.**")

        difficulties = st.multiselect(
            "Difficulty",
            options=data.DIFFICULTIES,
            default=data.DIFFICULTIES,
            key="sql_diff_filter",
        )
        c1, c2 = st.columns(2)
        with c1:
            shuffle_q = st.checkbox(
                "Shuffle questions", value=True, key="sql_shuffle_q"
            )
        with c2:
            shuffle_a = st.checkbox(
                "Shuffle answers", value=True, key="sql_shuffle_a"
            )

        pool = sql_df[sql_df["difficulty"].isin({d.lower() for d in difficulties})]
        st.caption(f"Pool: **{len(pool)}** question(s)")

        if st.button(
            "🚀 Start SQL quiz",
            type="primary",
            disabled=pool.empty,
            key="sql_start_btn",
        ):
            state.start_quiz(
                pool.index.tolist(), shuffle_q, shuffle_a, prefix=SQL_PREFIX
            )
            st.rerun()
        return

    if st.button("🔄 Restart SQL quiz", key="sql_restart_btn"):
        state.reset_quiz(SQL_PREFIX)
        st.rerun()

    quiz_engine.render_question_flow(sql_df, prefix=SQL_PREFIX)


# --------------------------------------------------------------------------- #
#  Write SQL tab (free-form, checked against a reference result set)
# --------------------------------------------------------------------------- #
def _render_write_tab() -> None:
    st.markdown(
        "Write your own query for each task. It runs against a **fresh copy** "
        "of the sample warehouse and is compared with a reference result set. "
        "Column *names* are ignored (aliases are fine), column *order* and row "
        "values matter, and row order only matters when the task says so."
    )

    wstate = st.session_state.setdefault(
        "sql_write_state",
        {"solved": set(), "attempts": {}, "queries": {}, "results": {}},
    )
    solved = wstate["solved"]
    ids = [c.id for c in CHALLENGES]

    # Deferred widget updates — must happen before the widgets are created.
    if wstate.get("next_pick"):
        st.session_state["sql_write_pick"] = wstate.pop("next_pick")

    if st.session_state.get("sql_write_pick") not in ids:
        st.session_state["sql_write_pick"] = next(
            (cid for cid in ids if cid not in solved), ids[0]
        )

    st.progress(
        len(solved) / len(ids),
        text=f"Solved **{len(solved)} / {len(ids)}** challenges",
    )

    def _label(cid: str) -> str:
        ch = get_challenge(cid)
        return f"{'✅' if cid in solved else '⬜'} {ch.title} · {ch.difficulty}"

    cid = st.selectbox(
        "Challenge", options=ids, format_func=_label, key="sql_write_pick"
    )
    ch = get_challenge(cid)

    with st.container(border=True):
        st.markdown(f"#### {ch.title}")
        st.caption(
            f"Difficulty: **{ch.difficulty}** · Tables: "
            + ", ".join(f"`{t}`" for t in ch.tables)
        )
        st.markdown(ch.prompt)
        if ch.ordered:
            st.caption("⚠️ **Row order matters** for this task.")

    if ch.hint:
        with st.expander("💡 Hint"):
            st.markdown(ch.hint)

    input_key = f"sql_write_input_{cid}"
    if wstate.pop("clear_for", None) == cid:
        wstate["queries"].pop(cid, None)
        wstate["results"].pop(cid, None)
        st.session_state.pop(input_key, None)

    if input_key not in st.session_state:
        st.session_state[input_key] = wstate["queries"].get(cid, "")

    sql = st.text_area(
        "Your query", key=input_key, height=220, placeholder="SELECT ..."
    )
    wstate["queries"][cid] = sql

    col_run, col_clear, _ = st.columns([1, 1, 3])
    with col_run:
        run = st.button("▶️ Check query", type="primary", key=f"sqlw_run_{cid}")
    with col_clear:
        clear = st.button("🧹 Clear", key=f"sqlw_clear_{cid}")
    st.caption("Only a single read-only `SELECT` / `WITH` statement is accepted.")

    if clear:
        wstate["clear_for"] = cid
        st.rerun()

    if run:
        if not sql.strip():
            st.warning("Write a query first.")
        else:
            outcome = evaluate(ch, sql)
            wstate["results"][cid] = {"sql": sql.strip(), "outcome": outcome}
            wstate["attempts"][cid] = wstate["attempts"].get(cid, 0) + 1
            if outcome.ok:
                solved.add(cid)
            st.rerun()

    entry = wstate["results"].get(cid)
    if entry is not None:
        outcome = entry["outcome"]
        if entry["sql"] != sql.strip():
            st.info("The query changed since the last check — run it again.")

        if outcome.ok:
            st.success(
                "✅ **Correct.** Your query returns exactly the expected result set."
            )
        else:
            st.error(outcome.message)

        if outcome.user_df is not None:
            with st.expander(
                f"Your output ({len(outcome.user_df)} row(s))",
                expanded=not outcome.ok,
            ):
                st.dataframe(
                    outcome.user_df.head(100),
                    use_container_width=True,
                    hide_index=True,
                )
                if len(outcome.user_df) > 100:
                    st.caption("Showing the first 100 rows.")

        if not outcome.ok and outcome.ref_df is not None:
            with st.expander("Expected output"):
                st.dataframe(
                    outcome.ref_df.head(100),
                    use_container_width=True,
                    hide_index=True,
                )
                if len(outcome.ref_df) > 100:
                    st.caption("Showing the first 100 rows.")

        if outcome.missing:
            st.markdown("**Rows the expected result has but yours does not:**")
            st.dataframe(
                pd.DataFrame(
                    outcome.missing, columns=list(outcome.ref_df.columns)
                ).head(10),
                use_container_width=True,
                hide_index=True,
            )

        if outcome.extra:
            st.markdown("**Rows in your result that should not be there:**")
            st.dataframe(
                pd.DataFrame(
                    outcome.extra, columns=list(outcome.user_df.columns)
                ).head(10),
                use_container_width=True,
                hide_index=True,
            )

    attempts = wstate["attempts"].get(cid, 0)
    if cid in solved or attempts >= 2:
        with st.expander("🧑‍🏫 Reference solution"):
            st.code(ch.reference_sql, language="sql")
    else:
        st.caption(
            "The reference solution unlocks once you solve the challenge "
            "or after two attempts."
        )

    if cid in solved:
        idx = ids.index(cid)
        if idx + 1 < len(ids):
            if st.button("Next challenge ➡️", key=f"sqlw_next_{cid}"):
                wstate["next_pick"] = ids[idx + 1]
                st.rerun()


# --------------------------------------------------------------------------- #
#  Playground tab
# --------------------------------------------------------------------------- #
def _render_playground_tab() -> None:
    st.markdown(
        "Write SQL against the sample warehouse (SQLite). Only read-only "
        "queries are allowed. Table definitions and sample rows are in the "
        "**Schema** tab."
    )

    if "sql_playground_query" not in st.session_state:
        st.session_state["sql_playground_query"] = DEFAULT_QUERY

    query = st.text_area(
        "SQL query",
        height=200,
        key="sql_playground_query",
        placeholder="SELECT * FROM orders WHERE amount > 100;",
    )
    st.caption(
        "Try: `SELECT * FROM orders;` · "
        "`SELECT c.name, SUM(o.amount) FROM customers c JOIN orders o "
        "ON o.customer_id = c.customer_id GROUP BY c.name;`"
    )

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        run = st.button("▶️ Run", type="primary", key="sql_run_btn")
    with c2:
        reset_query = st.button("🔄 Reset query", key="sql_reset_query_btn")
    with c3:
        reset_db_btn = st.button("🗑️ Reset DB", key="sql_reset_db_btn")

    if reset_query:
        st.session_state["sql_playground_query"] = DEFAULT_QUERY
        st.rerun()

    if reset_db_btn:
        reset_db()
        st.success("Sample database reset.")
        st.rerun()

    if run:
        guard = check_read_only(query)
        if guard:
            st.error(guard)
            return
        try:
            conn = get_db()
            result = pd.read_sql_query(query, conn)
            st.success(f"{len(result)} row(s) returned")
            st.dataframe(result, use_container_width=True, hide_index=True)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Query error: `{exc}`")


# --------------------------------------------------------------------------- #
#  Cheatsheet tab  (unchanged)
# --------------------------------------------------------------------------- #
def _render_cheatsheet_tab() -> None:
    st.markdown(
        "The SQL patterns that come up most often in DS / consulting "
        "interviews."
    )

    _cheat_section(
        "1. Keep the latest row per group (deduplication)",
        "`ROW_NUMBER() OVER (PARTITION BY key ORDER BY date DESC)`",
        """SELECT *
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY customer_id
               ORDER BY order_date DESC
           ) AS rn
    FROM orders
) t
WHERE rn = 1;""",
        "**Why it wins:** `SELECT DISTINCT` keeps an arbitrary row when other "
        "columns differ. `GROUP BY` loses non-key columns. The window "
        "function is deterministic and preserves every column.",
    )

    _cheat_section(
        "2. Find records missing in another table (anti-join)",
        "`LEFT JOIN ... WHERE right.key IS NULL`, or `NOT EXISTS`",
        """-- Customers with no orders
SELECT c.*
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;""",
        "**Why it wins:** `NOT IN` is dangerous — if the subquery returns any "
        "NULL, the whole predicate becomes NULL and returns no rows. "
        "`NOT EXISTS` is often the safest and most performant.",
    )

    _cheat_section(
        "3. Running total / moving average",
        "`SUM(...) OVER (PARTITION BY ... ORDER BY ... ROWS BETWEEN ...)`",
        """SELECT
    customer_id,
    order_date,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
        ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total,
    AVG(amount) OVER (
        PARTITION BY customer_id
        ORDER BY order_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3
FROM orders;""",
        "**Why it wins:** self-joins or correlated subqueries compute the "
        "same thing but are slower and harder to read. Always specify "
        "`ROWS BETWEEN ...` — the default frame can surprise you.",
    )

    _cheat_section(
        "4. Row number vs. rank vs. dense rank",
        "`ROW_NUMBER` / `RANK` / `DENSE_RANK`",
        """SELECT
    customer_id,
    amount,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY amount DESC) AS rn,
    RANK()       OVER (PARTITION BY customer_id ORDER BY amount DESC) AS rnk,
    DENSE_RANK() OVER (PARTITION BY customer_id ORDER BY amount DESC) AS drnk
FROM orders;""",
        "**Difference:** for ties, `ROW_NUMBER` gives 1, 2, 3…; `RANK` gives "
        "1, 1, 3…; `DENSE_RANK` gives 1, 1, 2… Use `RANK` for 'top N per "
        "group' where ties should be included.",
    )

    _cheat_section(
        "5. Grain issues — fan-out from joins",
        "Join on the correct grain, or pre-aggregate",
        """-- Buggy: inflates revenue because one order has many items
SELECT o.customer_id, SUM(o.amount) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.customer_id;

-- Correct: aggregate items first, then join
SELECT o.customer_id, SUM(o.amount) AS revenue
FROM orders o
LEFT JOIN (
    SELECT order_id, SUM(quantity * unit_price) AS items_total
    FROM order_items
    GROUP BY order_id
) oi ON oi.order_id = o.order_id
GROUP BY o.customer_id;""",
        "**Why it bites:** every one-to-many join replicates the parent row. "
        "If you `SUM` a parent column across the join, you double-count. "
        "Always know the grain of each table before joining.",
    )

    _cheat_section(
        "6. NULL handling in comparisons",
        "`IS NULL` / `IS NOT NULL`; `COALESCE` for defaults",
        """SELECT *
FROM customers
WHERE country IS NULL;

SELECT
    customer_id,
    COALESCE(country, 'UNKNOWN') AS country_clean
FROM customers;""",
        "**Watch out:** `col = NULL` is never true, and `col <> 'x'` silently "
        "excludes NULL rows. This is the #1 source of 'missing rows' bugs "
        "in analytics SQL.",
    )

    _cheat_section(
        "7. Cohort retention",
        "First-purchase month + subsequent activity",
        """WITH first_order AS (
    SELECT customer_id,
           MIN(order_date) AS first_date
    FROM orders
    GROUP BY customer_id
)
SELECT
    strftime('%Y-%m', fo.first_date) AS cohort,
    strftime('%Y-%m', o.order_date)  AS activity_month,
    COUNT(DISTINCT o.customer_id)    AS active_customers
FROM orders o
JOIN first_order fo USING (customer_id)
GROUP BY cohort, activity_month
ORDER BY cohort, activity_month;""",
        "**Why it's asked:** cohort retention is the bread-and-butter of "
        "marketing analytics at Jakala and Artefact. Get the two-step "
        "pattern (first-date per user, then join and group) into muscle "
        "memory.",
    )


def _cheat_section(title: str, pattern: str, code: str, note: str) -> None:
    with st.expander(title, expanded=False):
        st.markdown(f"**Pattern:** {pattern}")
        st.code(code, language="sql")
        st.markdown(note)


# --------------------------------------------------------------------------- #
#  Schema tab
# --------------------------------------------------------------------------- #
def _render_schema_tab() -> None:
    st.markdown(
        "Sample warehouse available in the **Write SQL** and **Playground** "
        "tabs. All tables live in an in-memory SQLite database."
    )

    for name, tbl in SAMPLE_DATA.items():
        with st.expander(f"`{name}` — {len(tbl['rows'])} rows", expanded=False):
            st.code(tbl["schema"], language="sql")
            st.dataframe(
                pd.DataFrame(tbl["rows"], columns=tbl["columns"]),
                use_container_width=True,
                hide_index=True,
            )