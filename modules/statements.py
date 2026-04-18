import json
import streamlit as st
import pandas as pd
from components.progress import init_progress, record_score, mark_module_complete, MODULES
from components.feedback import grade_questions

MODULE_KEY = "statements"


def _load_scenarios() -> list:
    with open("scenarios/statements.json") as f:
        return json.load(f)


def _render_table(financial_data: dict) -> None:
    st.markdown(f"**{financial_data['title']}**")
    rows = financial_data["rows"]
    columns = financial_data["columns"]
    df = pd.DataFrame(rows, columns=columns)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _collect_answers(questions: list) -> dict:
    answers = {}
    for q in questions:
        if q["type"] == "number":
            val = st.number_input(q["text"], min_value=0.0, step=0.1, key=f"input_{q['id']}")
            answers[q["id"]] = val
        elif q["type"] == "multiple_choice":
            val = st.radio(q["text"], options=q["options"], key=f"input_{q['id']}", index=None)
            answers[q["id"]] = val
    return answers


def render() -> None:
    init_progress()
    progress = st.session_state.progress
    scenarios = _load_scenarios()

    st.header("Module 1: Financial Statements")
    st.caption("Learn to read and interpret P&L, balance sheet, and cash flow statements.")

    scenario_idx = st.session_state.get("stmt_scenario_idx", 0)
    if scenario_idx >= len(scenarios):
        st.success("Module complete! All scenarios finished.")
        progress = mark_module_complete(progress, MODULE_KEY)
        st.session_state.progress = progress
        return

    scenario = scenarios[scenario_idx]
    st.subheader(f"Scenario {scenario_idx + 1} of {len(scenarios)}: {scenario['title']}")
    st.info(scenario["context"])

    _render_table(scenario["financial_data"])
    st.markdown("---")
    st.markdown("**Your answers:**")
    answers = _collect_answers(scenario["questions"])

    if st.button("Submit", key="stmt_submit"):
        if None in answers.values():
            st.warning("Please answer all questions before submitting.")
            return
        signal, feedback = grade_questions(scenario["questions"], answers)
        progress = record_score(progress, MODULE_KEY, scenario_idx, signal)
        st.session_state.progress = progress

        if signal == "pass":
            st.success(f"Pass — {feedback}")
        elif signal == "partial":
            st.warning(f"Partial — {feedback}")
        else:
            st.error(f"Incorrect — {feedback}")

        if signal in ("pass", "partial"):
            if st.button("Next scenario →", key="stmt_next"):
                st.session_state.stmt_scenario_idx = scenario_idx + 1
                st.rerun()
        else:
            if st.button("Try again", key="stmt_retry"):
                st.rerun()
