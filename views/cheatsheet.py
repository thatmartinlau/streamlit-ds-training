"""ML fundamentals cheat sheet page."""

import streamlit as st

from core.cheatsheet_data import CHEATSHEETS


_TABLE_CSS = """
<style>
.ml-cheat-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    margin: 0.5rem 0 1.5rem 0;
    table-layout: fixed;
    color: inherit;
}
.ml-cheat-table th {
    /* Fallback (neutral gray, readable on light and dark), then a
       theme-aware tint derived from the active text color. */
    background: rgba(128, 128, 128, 0.18);
    background: color-mix(in srgb, currentColor 12%, transparent);
    text-align: left;
    padding: 10px;
    border: 1px solid rgba(128, 128, 128, 0.35);
    border-color: color-mix(in srgb, currentColor 28%, transparent);
    vertical-align: top;
    font-weight: 600;
    color: inherit;
}
.ml-cheat-table td {
    padding: 10px;
    border: 1px solid rgba(128, 128, 128, 0.25);
    border-color: color-mix(in srgb, currentColor 20%, transparent);
    vertical-align: top;
    word-wrap: break-word;
    overflow-wrap: anywhere;
    color: inherit;
    background: transparent;
}
.ml-cheat-table tbody tr:nth-child(even) td {
    background: rgba(128, 128, 128, 0.07);
    background: color-mix(in srgb, currentColor 5%, transparent);
}
</style>
"""

def _render_table(columns: list[str], rows: list[list[str]], widths: list[str]) -> None:
    colgroup = "".join(f'<col style="width:{w}">' for w in widths)
    header = "".join(f"<th>{c}</th>" for c in columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    html = (
        f'<table class="ml-cheat-table">'
        f"<colgroup>{colgroup}</colgroup>"
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{body}</tbody>"
        f"</table>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render() -> None:
    st.title("📋 ML Fundamentals Cheatsheet")
    st.markdown(
        "Quick-reference tables for the algorithms, metrics, and validation "
        "strategies that come up most often in DS / ML interviews. "
        "Use the tabs to jump to a topic."
    )

    st.markdown(_TABLE_CSS, unsafe_allow_html=True)

    labels = list(CHEATSHEETS.keys())
    tabs = st.tabs(labels)

    for tab, label in zip(tabs, labels):
        section = CHEATSHEETS[label]
        with tab:
            st.markdown(section["description"])
            _render_table(
                section["columns"],
                section["rows"],
                section["widths"],
            )