import json
import streamlit as st
import pandas as pd
from components.progress import init_progress, record_score, mark_module_complete
from components.feedback import get_ai_feedback, grade_table_input

MODULE_KEY = "forecasting"
SCORE_VALUES = {"pass": 2, "partial": 1, "fail": 0}


def _load_scenarios() -> list:
    with open("scenarios/forecasting.json") as f:
        return json.load(f)


def _render_table(financial_data: dict) -> None:
    st.markdown(f"**{financial_data['title']}**")
    df = pd.DataFrame(financial_data["rows"], columns=financial_data["columns"])
    st.dataframe(df, use_container_width=True, hide_index=True)


def _combined_signal(number_signal: str, ai_signal: str) -> str:
    combined = (SCORE_VALUES[number_signal] + SCORE_VALUES[ai_signal]) / 2
    if combined >= 1.5:
        return "pass"
    elif combined >= 0.75:
        return "partial"
    return "fail"


def render() -> None:
    init_progress()
    progress = st.session_state.progress
    scenarios = _load_scenarios()

    st.header("Module 4: Forecasting")
    st.caption("Update rolling forecasts and explain your assumptions.")

    scenario_idx = st.session_state.get("fore_scenario_idx", 0)
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

    answer_type = scenario.get("answer_type", "text")

    number_answers = {}
    if answer_type == "hybrid":
        st.markdown("**Update the forecast numbers:**")
        for field in scenario["number_fields"]:
            val = st.number_input(field["label"], min_value=0, step=10, key=f"fore_num_{field['id']}")
            number_answers[field["id"]] = val
        st.markdown("---")

    st.markdown(f"**Task:** {scenario['prompt']}")
    text_answer = st.text_area(
        "Your explanation:",
        height=150,
        key=f"fore_text_{scenario_idx}",
        placeholder="Write your rationale here...",
    )

    if st.button("Submit", key="fore_submit"):
        if not text_answer.strip():
            st.warning("Please write an explanation before submitting.")
        else:
            with st.spinner("Evaluating your answer..."):
                ai_result = get_ai_feedback(scenario, text_answer)

            if answer_type == "hybrid":
                number_signal, number_feedback = grade_table_input(scenario["number_fields"], number_answers)
                final_signal = _combined_signal(number_signal, ai_result["signal"])
                ai_result["number_feedback"] = number_feedback
            else:
                final_signal = ai_result["signal"]

            progress = record_score(progress, MODULE_KEY, scenario_idx, final_signal)
            st.session_state.progress = progress
            st.session_state["fore_result"] = (final_signal, ai_result)
            st.rerun()

    stored = st.session_state.get("fore_result")
    if stored:
        final_signal, ai_result = stored
        if "number_feedback" in ai_result:
            st.markdown(f"**Numbers:** {ai_result['number_feedback']}")

        if final_signal == "pass":
            st.success("Pass")
        elif final_signal == "partial":
            st.warning("Partial")
        else:
            st.error("Not quite")

        st.markdown(f"**Feedback:** {ai_result['feedback']}")
        st.markdown(f"**Tip:** {ai_result['tip']}")

        if final_signal in ("pass", "partial"):
            if st.button("Next scenario →", key="fore_next"):
                st.session_state.fore_scenario_idx = scenario_idx + 1
                st.session_state.pop("fore_result", None)
                st.rerun()
        else:
            if st.button("Try again", key="fore_retry"):
                st.session_state.pop("fore_result", None)
                st.rerun()
