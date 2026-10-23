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
from views import pandas as pandas_view
from views import cheatsheet as cheatsheet_view
from views import stats as stats_view
from views import dynamic_quiz as dynamic_quiz_view


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
    st.Page(
        pandas_view.render, 
        title="Pandas Training", 
        icon="🐼", 
        url_path="pandas"),
    st.Page(
        cheatsheet_view.render,
        title="ML Cheatsheet",
        icon="📋",
        url_path="cheatsheet",
    ),
    st.Page(
        stats_view.render,
        title="Stats Cheatsheet",
        icon="📋",
        url_path="stats",
    ),
    st.Page(
        dynamic_quiz_view.render,
        title="Dynamic Screen",
        icon="✨",
        url_path="dynamic-screen",
    ),
]

st.navigation(NAV_PAGES).run()