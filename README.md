# streamlit-ds-training

Data science / ML / AI-consulting interview prep built with Streamlit.

## Pages

- **Welcome** – overview and CSV schema for the multiple-choice question bank.
- **Quiz** – multiple-choice questions loaded from `questions.csv` (or an upload).
- **SQL Training**
  - **Quiz** – multiple-choice SQL questions (theme `SQL & Data Manipulation`).
  - **Write SQL** – free-form challenges: type a query, it is executed against a
    fresh copy of the sample warehouse and compared with a reference result set
    (column count and row values must match; column names are ignored; row order
    only matters when the task says so). Includes per-challenge hints, expected
    output on failure, and a reference solution.
  - **Playground** – run ad-hoc read-only queries.
  - **Cheatsheet** – the SQL patterns that show up most in interviews.
  - **Schema** – the sample warehouse tables and rows.

## Run

```bash
streamlit run app.py
```

---

## Notes on the checker

- Both queries run on a **fresh `build_db()`** connection, so nothing a submitted query does can corrupt your session's playground DB.
- Results are compared as multisets of tuples after rounding floats to 6 decimals and mapping `NaN → NULL`. So `SELECT amount` and `SELECT CAST(amount AS REAL)` match, and aliases like `AS total_revenue` don't matter.
- Column **order** does matter (positional comparison) — tasks state the expected column order explicitly.
- For unordered tasks, adding `ORDER BY` is harmless. For ordered tasks the prompt always pins down the tie-breaker (e.g. "break ties by the lower `order_id`") so the reference is deterministic.
- `check_read_only()` blocks multiple statements and DML/DDL keywords (outside string literals), and the Playground now uses the same guard.
- Hardcoding a literal result is technically possible, but with 48 orders / 22 customers / 82 items it is far more work than writing the query — which is the point.