import json
import streamlit as st
import pandas as pd
from components.progress import init_progress, record_score, mark_module_complete
from components.feedback import get_ai_feedback

MODULE_KEY = "variance"


def _load_scenarios() -> list:
    with open("scenarios/variance.json") as f:
        return json.load(f)


def _render_variance_table(financial_data: dict) -> None:
    st.markdown(f"**{financial_data['title']}**")
    df = pd.DataFrame(financial_data["rows"], columns=financial_data["columns"])
    st.dataframe(df, use_container_width=True, hide_index=True)


def render() -> None:
    init_progress()
    progress = st.session_state.progress
    scenarios = _load_scenarios()

    st.header("Module 3: Variance Analysis")
    st.caption("Compare actuals vs. budget and write CFO-ready explanations.")

    scenario_idx = st.session_state.get("var_scenario_idx", 0)
    if scenario_idx >= len(scenarios):
        st.success("Module complete! All scenarios finished.")
        progress = mark_module_complete(progress, MODULE_KEY)
        st.session_state.progress = progress
        return

    scenario = scenarios[scenario_idx]
    st.subheader(f"Scenario {scenario_idx + 1} of {len(scenarios)}: {scenario['title']}")
    st.info(scenario["context"])

    _render_variance_table(scenario["financial_data"])
    st.markdown("---")
    st.markdown(f"**Task:** {scenario['prompt']}")

    answer = st.text_area(
        "Your explanation:",
        height=150,
        key=f"var_answer_{scenario_idx}",
        placeholder="Write your variance explanation here...",
    )

    if st.button("Submit", key="var_submit"):
        if not answer.strip():
            st.warning("Please write an explanation before submitting.")
            return

        with st.spinner("Evaluating your answer..."):
            result = get_ai_feedback(scenario, answer)

        signal = result["signal"]
        progress = record_score(progress, MODULE_KEY, scenario_idx, signal)
        st.session_state.progress = progress

        if signal == "pass":
            st.success("Pass")
        elif signal == "partial":
            st.warning("Partial")
        else:
            st.error("Not quite")

        st.markdown(f"**Feedback:** {result['feedback']}")
        st.markdown(f"**Tip:** {result['tip']}")

        if signal in ("pass", "partial"):
            if st.button("Next scenario →", key="var_next"):
                st.session_state.var_scenario_idx = scenario_idx + 1
                st.rerun()
        else:
            if st.button("Try again", key="var_retry"):
                st.rerun()
