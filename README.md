# streamlit-ds-training

Data science / ML / AI-consulting interview prep built with Streamlit.

## Pages

- **Welcome** – overview, CSV schema, and the list of loaded question files.
- **Quiz** – multiple-choice questions from the bundled question directory
  (or an upload).
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

## Question bank

Question CSVs live in `quiz_questions/`. **Every `*.csv` in that folder is
loaded and merged into a single pool** — split your bank however you like
(by topic, difficulty, vertical, ...). The folder is created automatically if
it doesn't exist.

Required CSV schema (see the Welcome page for details):

```
question,answer1,answer2,answer3,answer4,correctanswer,explanation,theme,
difficulty,secondary_themes,vertical
```


Files that don't match the schema are **skipped with a warning**; the remaining
files still load. Click **🔄 Reload from quiz_questions/** in the sidebar to
re-scan the folder (also clears the CSV read cache, so edits to files on disk
are picked up). Uploading a CSV in the sidebar **replaces** the bundled pool for
the current session.

## Run

```bash
streamlit run app.py
```


---

## Notes

- **Backwards compatible with uploads**: uploading a CSV still replaces the pool (as before). The signature check now lives in `df_upload_sig` so re-scanning the directory won't spuriously reload the same upload.
- **Per-file failures are non-fatal**: a malformed CSV is recorded in `df_errors` and shown in the sidebar / Welcome page, but every other file still loads. If *every* file fails, `df` is `None` and the app tells you why.
- **Empty folders are not errors that block uploads** — the Quiz page still lets you upload a CSV even when `quiz_questions/` is empty.
- **Cache**: `reload_from_dir()` calls `read_csv_from_path.clear()`, which invalidates only the file-read cache (not unrelated `st.cache_data` consumers).