"""
ML / DS / AI Consulting interview prep — entry point.

Run with:
    streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="ML / DS / AI Interview Prep",
    page_icon="🧠",
    layout="wide",
)

from core import data  # noqa: E402
from views import quiz, sql, welcome  # noqa: E402

data.init_session()

NAV_PAGES = [
    st.Page(
        welcome.render,
        title="Welcome",
        icon="🏠",
        url_path="welcome",
        default=True,
    ),
    st.Page(
        quiz.render,
        title="Quiz",
        icon="🧠",
        url_path="quiz",
    ),
    st.Page(
        sql.render,
        title="SQL Training",
        icon="🗄️",
        url_path="sql",
    ),
]

st.navigation(NAV_PAGES).run()