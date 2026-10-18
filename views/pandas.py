"""Pandas training page: code challenges against the Titanic dataset."""

import pandas as pd
import streamlit as st

from core import pandas_challenges as pc
from core import pandas_data as pdata


def render() -> None:
    pdata.init_session()

    with st.sidebar:
        _render_sidebar()

    st.title("🐼 Pandas Training")
    st.markdown(
        "Practice pandas by **writing real code**. Each challenge runs your "
        "expression against the **Titanic** dataset and compares the output "
        "with a reference answer — DataFrames, Series, scalars and lists all "
        "work."
    )

    df = pdata.get_df()
    if df is None:
        st.warning(
            "No Titanic dataset loaded. Drop a `titanic.csv` in the repo root "
            "(or `data/`), or upload one in the sidebar."
        )
        return

    challenges, errors = pc.load_challenges()
    if errors:
        with st.expander("⚠️ Some question files were skipped"):
            for err in errors:
                st.caption(f"`{err['file']}` — {err['error']}")

    if not challenges:
        st.info(
            "No challenge files found. Add CSVs to `pandas_questions/` "
            "(see the README for the schema)."
        )
        return

    tab_ch, tab_data, tab_cheat = st.tabs(["✍️ Challenges", "📊 Data", "📚 Cheatsheet"])
    with tab_ch:
        _render_challenges_tab(df, challenges)
    with tab_data:
        _render_data_tab(df)
    with tab_cheat:
        _render_cheatsheet_tab()


# --------------------------------------------------------------------------- #
#  Sidebar
# --------------------------------------------------------------------------- #
def _render_sidebar() -> None:
    st.header("🐼 Titanic dataset")

    uploaded = st.file_uploader(
        "Upload titanic.csv", type=["csv"], key="pandas_uploader"
    )
    if (
        uploaded is not None
        and uploaded.name != st.session_state.get("_titanic_upload_sig")
    ):
        try:
            pdata.set_df(pd.read_csv(uploaded), uploaded.name)
            st.session_state["_titanic_upload_sig"] = uploaded.name
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not read the uploaded CSV: {exc}")

    if st.button("🔄 Reload from disk", use_container_width=True, key="pandas_reload"):
        pdata.reload_from_disk()
        st.rerun()

    df = pdata.get_df()
    if df is not None:
        st.caption(f"Loaded `{pdata.get_source()}` — {len(df)} rows × {df.shape[1]} cols")
    else:
        st.caption("No dataset loaded.")


# --------------------------------------------------------------------------- #
#  Challenges tab
# --------------------------------------------------------------------------- #
def _render_challenges_tab(df: pd.DataFrame, challenges: list[pc.PandasChallenge]) -> None:
    by_id = {c.id: c for c in challenges}
    ids = [c.id for c in challenges]

    wstate = st.session_state.setdefault(
        "pandas_write_state",
        {"solved": set(), "attempts": {}, "queries": {}, "results": {}},
    )
    solved = wstate["solved"]

    if wstate.get("next_pick"):
        st.session_state["pandas_pick"] = wstate.pop("next_pick")
    if st.session_state.get("pandas_pick") not in ids:
        st.session_state["pandas_pick"] = next(
            (cid for cid in ids if cid not in solved), ids[0]
        )

    st.progress(
        len(solved) / len(ids),
        text=f"Solved **{len(solved)} / {len(ids)}** challenges",
    )

    def _label(cid: str) -> str:
        ch = by_id[cid]
        return f"{'✅' if cid in solved else '⬜'} {ch.title} · {ch.difficulty}"

    cid = st.selectbox("Challenge", options=ids, format_func=_label, key="pandas_pick")
    ch = by_id[cid]

    with st.container(border=True):
        st.markdown(f"#### {ch.title}")
        st.caption(f"Difficulty: **{ch.difficulty}**")
        st.markdown(ch.prompt)
        if ch.ordered:
            st.caption("⚠️ **Row order matters** for this task.")

    if ch.hint:
        with st.expander("💡 Hint"):
            st.markdown(ch.hint)

    input_key = f"pandas_input_{cid}"
    if wstate.pop("clear_for", None) == cid:
        wstate["queries"].pop(cid, None)
        wstate["results"].pop(cid, None)
        st.session_state.pop(input_key, None)

    if input_key not in st.session_state:
        st.session_state[input_key] = wstate["queries"].get(cid, "")

    code = st.text_area(
        "Your pandas code",
        key=input_key,
        height=200,
        placeholder="e.g. df[df['Age'] > 30]",
    )
    wstate["queries"][cid] = code
    st.caption(
        "`df` is the Titanic DataFrame and `pd` is imported. End with an "
        "expression — the value of the last line is what gets checked."
    )

    c_run, c_clear, _ = st.columns([1, 1, 3])
    with c_run:
        run = st.button("▶️ Check code", type="primary", key=f"pandas_run_{cid}")
    with c_clear:
        clear = st.button("🧹 Clear", key=f"pandas_clear_{cid}")

    if clear:
        wstate["clear_for"] = cid
        st.rerun()

    if run:
        if not code.strip():
            st.warning("Write some code first.")
        else:
            outcome = pc.evaluate(ch, code, df)
            wstate["results"][cid] = {"code": code.strip(), "outcome": outcome}
            wstate["attempts"][cid] = wstate["attempts"].get(cid, 0) + 1
            if outcome.ok:
                solved.add(cid)
            st.rerun()

    entry = wstate["results"].get(cid)
    if entry is not None:
        outcome = entry["outcome"]
        if entry["code"] != code.strip():
            st.info("Your code changed since the last check — run it again.")

        if outcome.ok:
            st.success("✅ **Correct.** Your output matches the reference.")
        else:
            st.error(outcome.message)

        if outcome.user_output is not None:
            with st.expander(
                "Your output", expanded=not outcome.ok
            ):
                _render_output(outcome.user_output)

        if not outcome.ok and outcome.ref_output is not None:
            with st.expander("Expected output"):
                _render_output(outcome.ref_output)

        if outcome.missing and outcome.ref_output is not None:
            st.markdown("**Rows the expected output has but yours does not:**")
            cols = _columns_of(outcome.ref_output)
            st.dataframe(
                pd.DataFrame(outcome.missing, columns=cols).head(10),
                use_container_width=True, hide_index=True,
            )
        if outcome.extra and outcome.user_output is not None:
            st.markdown("**Rows in your output that should not be there:**")
            cols = _columns_of(outcome.user_output)
            st.dataframe(
                pd.DataFrame(outcome.extra, columns=cols).head(10),
                use_container_width=True, hide_index=True,
            )

    attempts = wstate["attempts"].get(cid, 0)
    if cid in solved or attempts >= 2:
        with st.expander("🧑‍🏫 Reference solution"):
            st.code(ch.reference_code, language="python")
    else:
        st.caption(
            "The reference solution unlocks once you solve the challenge "
            "or after two attempts."
        )

    if cid in solved:
        idx = ids.index(cid)
        if idx + 1 < len(ids):
            if st.button("Next challenge ➡️", key=f"pandas_next_{cid}"):
                wstate["next_pick"] = ids[idx + 1]
                st.rerun()


def _columns_of(obj) -> list:
    if isinstance(obj, pd.DataFrame):
        return list(obj.columns)
    if isinstance(obj, pd.Series):
        return [obj.name if obj.name is not None else "value"]
    return ["value"]


def _render_output(obj) -> None:
    if isinstance(obj, pd.DataFrame):
        st.dataframe(obj.head(50), use_container_width=True)
        if len(obj) > 50:
            st.caption(f"Showing first 50 of {len(obj)} rows.")
    elif isinstance(obj, pd.Series):
        st.dataframe(obj.head(50).to_frame(), use_container_width=True)
        if len(obj) > 50:
            st.caption(f"Showing first 50 of {len(obj)} rows.")
    else:
        st.code(repr(obj), language="python")


# --------------------------------------------------------------------------- #
#  Data tab
# --------------------------------------------------------------------------- #
def _render_data_tab(df: pd.DataFrame) -> None:
    st.markdown(f"**{len(df)} rows × {df.shape[1]} columns**")
    st.markdown("##### Preview")
    st.dataframe(df.head(20), use_container_width=True)
    st.markdown("##### Dtypes")
    st.dataframe(
        df.dtypes.astype(str).rename("dtype").to_frame(),
        use_container_width=True,
    )
    st.markdown("##### Missing values")
    st.dataframe(
        df.isna().sum().rename("n_missing").to_frame(),
        use_container_width=True,
    )


# --------------------------------------------------------------------------- #
#  Cheatsheet tab
# --------------------------------------------------------------------------- #
def _render_cheatsheet_tab() -> None:
    st.markdown("The pandas patterns that come up most often in DS interviews.")

    _cheat(
        "1. Select & filter",
        "`df[cols]` / `df[boolean_mask]` / `.loc` / `.query`",
        """# Multiple columns need a list (double brackets)
df[['Name', 'Age']]

# Boolean mask
df[df['Age'] > 30]

# Combine conditions — & / | / ~ (brackets required!)
df[(df['Sex'] == 'female') & (df['Pclass'] == 1)]

# .query() for readability
df.query("Age > 30 and Sex == 'female'")""",
        "**Watch out:** `df[df.Age > 30]` works but breaks on column names with "
        "spaces — prefer `df['Age']`. Always wrap each condition in parens "
        "when chaining with `&`/`|`.",
    )

    _cheat(
        "2. GroupBy: aggregation vs transform",
        "`groupby(...).agg(...)` vs `groupby(...).transform(...)`",
        """# One row per group
df.groupby('Pclass')['Fare'].mean()

# Multiple aggregations
df.groupby('Pclass')['Fare'].agg(['mean', 'median', 'count'])

# transform: same length as original — attaches group stat per row
df['fare_vs_class_mean'] = df.groupby('Pclass')['Fare'].transform('mean')""",
        "**Rule of thumb:** `agg` shrinks rows, `transform` keeps them. For "
        "adding a group-level stat back to each row, use `transform` — "
        "`merge` is slower and clunkier.",
    )

    _cheat(
        "3. Top-N per group",
        "`groupby(...).idxmax()` or `nlargest` per group",
        """# Row of the highest Fare per class
df.loc[df.groupby('Pclass')['Fare'].idxmax()]

# Top 2 per group
df.sort_values('Fare', ascending=False).groupby('Pclass').head(2)

# Or with nlargest per group
df.groupby('Pclass', group_keys=False).apply(lambda g: g.nlargest(2, 'Fare'))""",
        "**Why `idxmax`:** returns the label of the max in each group, so "
        "`df.loc[...]` gives you the full row. `nlargest` returns the values "
        "directly and is cleaner when you only need the top-k.",
    )

    _cheat(
        "4. Ranking within groups",
        "`groupby(...).rank(...)`",
        """df['fare_rank'] = df.groupby('Pclass')['Fare'].rank(
    ascending=False, method='min'
)""",
        "**Methods:** `average` (default), `min`, `max`, `dense`, `first`. "
        "Use `min` when tied values should share the best rank — the "
        "interview-safe default for 'top N' questions.",
    )

    _cheat(
        "5. Missing values",
        "`isna` / `fillna` / `dropna`",
        """df.isna().sum()                    # count per column
df.isna().mean() * 100             # percentage
df['Age'].fillna(df['Age'].median())
df.dropna(subset=['Age'])""",
        "**Note:** `df['Age'].mean()` skips NaN by default. `dropna` without "
        "arguments drops any row with any NaN — usually too aggressive.",
    )

    _cheat(
        "6. Merge & join",
        "`pd.merge(...)` with an explicit `on=`",
        """pd.merge(
    orders, customers,
    on='customer_id', how='left',
    validate='many_to_one',       # catches accidental fan-out
)""",
        "**Watch out:** `validate=` is your best friend — it raises if the "
        "join grain isn't what you expected. Fan-out from one-to-many joins "
        "silently inflates aggregates.",
    )

    _cheat(
        "7. String operations",
        "`.str.*` accessor",
        """df['Name'].str.split(',').str[0]            # surname
df['Name'].str.contains('Mrs', case=False)
df['Sex'].str.upper()""",
        "**Tip:** `.str` is vectorised C code — always prefer it to "
        "`.apply(lambda x: x.split(...))`.",
    )


def _cheat(title: str, pattern: str, code: str, note: str) -> None:
    with st.expander(title, expanded=False):
        st.markdown(f"**Pattern:** {pattern}")
        st.code(code, language="python")
        st.markdown(note)