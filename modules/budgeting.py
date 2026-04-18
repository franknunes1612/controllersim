import json
import streamlit as st
from components.progress import init_progress, record_score, mark_module_complete
from components.feedback import grade_table_input

MODULE_KEY = "budgeting"


def _load_scenarios() -> list:
    with open("scenarios/budgeting.json") as f:
        return json.load(f)


def _render_assumptions(financial_data: dict) -> None:
    st.markdown(f"**{financial_data['title']}**")
    for item in financial_data["items"]:
        st.markdown(f"- {item}")


def _collect_table_answers(fields: list) -> dict:
    answers = {}
    for field in fields:
        val = st.number_input(field["label"], min_value=0, step=1000, key=f"budg_{field['id']}")
        answers[field["id"]] = val
    return answers


def render() -> None:
    init_progress()
    progress = st.session_state.progress
    scenarios = _load_scenarios()

    st.header("Module 2: Budgeting")
    st.caption("Build department and headcount budgets from given assumptions.")

    scenario_idx = st.session_state.get("budg_scenario_idx", 0)
    if scenario_idx >= len(scenarios):
        st.success("Module complete! All scenarios finished.")
        progress = mark_module_complete(progress, MODULE_KEY)
        st.session_state.progress = progress
        return

    scenario = scenarios[scenario_idx]
    st.subheader(f"Scenario {scenario_idx + 1} of {len(scenarios)}: {scenario['title']}")
    st.info(scenario["context"])

    _render_assumptions(scenario["financial_data"])
    st.markdown("---")
    st.markdown("**Fill in the budget:**")
    answers = _collect_table_answers(scenario["fields"])

    if st.button("Submit", key="budg_submit"):
        signal, feedback = grade_table_input(scenario["fields"], answers)
        progress = record_score(progress, MODULE_KEY, scenario_idx, signal)
        st.session_state.progress = progress

        if signal == "pass":
            st.success(f"Pass — {feedback}")
        elif signal == "partial":
            st.warning(f"Partial — {feedback}")
        else:
            st.error(f"Incorrect — {feedback}")

        if signal in ("pass", "partial"):
            if st.button("Next scenario →", key="budg_next"):
                st.session_state.budg_scenario_idx = scenario_idx + 1
                st.rerun()
        else:
            if st.button("Try again", key="budg_retry"):
                st.rerun()
