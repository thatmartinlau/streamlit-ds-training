"""Statistics playbook — t-tests and A/B tests, course-notes style."""

import streamlit as st

from core.stats_notes import CARDS, StatCard


_PRIMER = """
Every t-test on this page has the **same three objects**. Only the
problem and the estimator change.

| Object | Definition | The question it answers |
|---|---|---|
| **Estimator** | A point estimate θ̂ of the target | *What's my best guess?* |
| **Confidence interval** | A range [L, U] such that θ falls inside with probability 1−α | *What's the plausible range?* |
| **Hypothesis test** | A p-value for H₀: θ = θ₀ | *Is θ₀ compatible with the data?* |

The two-sided test rejects H₀ at level α **iff** the corresponding
(1−α) two-sided CI excludes θ₀ — the p-value and the CI are two views
of the same calculation. Every card below applies that skeleton to a
different problem.
"""


def render() -> None:
    st.title("📐 Statistics Playbook")
    st.markdown(
        "Reference notes for the t-tests and A/B tests that come up in DS / "
        "ML interviews and consulting work. Each card shows the **math** "
        "(estimator, CI, hypothesis test), the assumptions it relies on, and "
        "when it wins or fails."
    )

    st.markdown(_PRIMER)

    st.markdown("**Contents**")
    for card in CARDS:
        st.markdown(f"- **{card.name}** — {card.tagline}")

    for card in CARDS:
        st.divider()
        _render_card(card)


def _render_card(card: StatCard) -> None:
    with st.container(border=True):
        st.markdown(f"### {card.name}")
        st.caption(f"_{card.tagline}_")
        st.markdown(card.intro)

        for block in card.math_blocks:
            st.markdown(f"**{block.label}**")
            st.latex(block.math)
            st.markdown(block.note)

        if card.assumptions:
            st.markdown("**Assumptions**")
            for a in card.assumptions:
                st.markdown(f"- {a}")

        if card.advantages or card.disadvantages:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Advantages**")
                for a in card.advantages:
                    st.markdown(f"- ✅ {a}")
            with c2:
                st.markdown("**Disadvantages**")
                for d in card.disadvantages:
                    st.markdown(f"- ⚠️ {d}")

        if card.code:
            st.markdown("**Code**")
            st.code(card.code, language="python")