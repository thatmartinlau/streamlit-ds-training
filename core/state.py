"""Session-state helpers for the quiz flow.

All keys are prefixed so multiple quizzes (general, SQL, ...) can run
independently within one session. `prefix=""` keeps the original bare keys,
so existing callers keep working unchanged.

NOTE: helper names are `get_state` / `set_state` (not `get` / `set`) so we
never shadow Python's builtin `set()`.
"""

import random

import streamlit as st


def _key(prefix: str, name: str) -> str:
    return f"{prefix}{name}" if prefix else name


def init_quiz_state(prefix: str = "") -> None:
    defaults = {
        "started": False,
        "quiz_id": 0,
        "order": [],
        "pos": 0,
        "responses": {},
        "revealed": set(),
        "answer_orders": {},
        "shuffle_answers": True,
    }
    for name, value in defaults.items():
        key = _key(prefix, name)
        if key not in st.session_state:
            st.session_state[key] = value


def get_state(prefix: str, name: str, default=None):
    return st.session_state.get(_key(prefix, name), default)


def set_state(prefix: str, name: str, value) -> None:
    st.session_state[_key(prefix, name)] = value


def start_quiz(
    pool_indices,
    shuffle_questions: bool,
    shuffle_answers: bool,
    *,
    prefix: str = "",
) -> None:
    order = list(pool_indices)
    if shuffle_questions:
        random.shuffle(order)

    st.session_state[_key(prefix, "quiz_id")] += 1
    st.session_state[_key(prefix, "order")] = order
    st.session_state[_key(prefix, "pos")] = 0
    st.session_state[_key(prefix, "responses")] = {}
    st.session_state[_key(prefix, "revealed")] = set()
    st.session_state[_key(prefix, "answer_orders")] = {}
    st.session_state[_key(prefix, "shuffle_answers")] = shuffle_answers
    st.session_state[_key(prefix, "started")] = True


def reset_quiz(prefix: str = "") -> None:
    set_state(prefix, "started", False)
    set_state(prefix, "order", [])
    set_state(prefix, "pos", 0)
    set_state(prefix, "responses", {})
    set_state(prefix, "revealed", set())
    set_state(prefix, "answer_orders", {})


def answer_order_for(qid, row, *, prefix: str = "") -> list:
    orders = st.session_state[_key(prefix, "answer_orders")]
    if qid not in orders:
        perm = [0, 1, 2, 3]
        if st.session_state[_key(prefix, "shuffle_answers")]:
            random.shuffle(perm)
        orders[qid] = perm
    return orders[qid]


def correct_position(qid, row, *, prefix: str = "") -> int:
    return st.session_state[_key(prefix, "answer_orders")][qid].index(
        int(row["correct_index"])
    )


def is_correct(qid, row, *, prefix: str = "") -> bool:
    return (
        st.session_state[_key(prefix, "responses")].get(qid)
        == correct_position(qid, row, prefix=prefix)
    )