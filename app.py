import streamlit as st
from components.progress import init_progress, is_module_unlocked, get_readiness_score, MODULES
from modules import statements, budgeting, variance, forecasting

st.set_page_config(page_title="ControllerSim — Nexova Ltd", page_icon="📊", layout="wide")

init_progress()
progress = st.session_state.progress

MODULE_LABELS = {
    "statements": "Module 1: Financial Statements",
    "budgeting": "Module 2: Budgeting",
    "variance": "Module 3: Variance Analysis",
    "forecasting": "Module 4: Forecasting",
}

# --- Sidebar ---
with st.sidebar:
    st.markdown("## 📊 ControllerSim")
    st.caption("Nexova Ltd — Controller Training")
    st.markdown("---")

    pages = ["Home"]
    for module_key in MODULES:
        label = MODULE_LABELS[module_key]
        if is_module_unlocked(progress, module_key):
            status = "✅" if progress[module_key]["completed"] else "▶️"
            pages.append(f"{status} {label}")
        else:
            pages.append(f"🔒 {label}")

    pages.append("About")
    page = st.radio("", pages, label_visibility="collapsed")

    st.markdown("---")
    score = get_readiness_score(progress)
    st.metric("Controller Readiness", f"{score}/100")

# --- Page routing ---
if page == "Home":
    st.title("Welcome to ControllerSim")
    st.markdown("""
You have just joined **Nexova Ltd** as a Junior Business Controller.

Your CFO has given you four training modules. Complete them in order to build your controller skill set.

| Module | Skills | Status |
|--------|--------|--------|
| 1 — Financial Statements | Read P&L, balance sheet, cash flow | Available |
| 2 — Budgeting | Build department and headcount budgets | Unlocks after Module 1 |
| 3 — Variance Analysis | Explain actuals vs. budget in writing | Unlocks after Module 2 |
| 4 — Forecasting | Update rolling forecasts with rationale | Unlocks after Module 3 |

Select a module from the sidebar to begin.
    """)

elif "Financial Statements" in page and "🔒" not in page:
    statements.render()

elif "Budgeting" in page and "🔒" not in page:
    budgeting.render()

elif "Variance Analysis" in page and "🔒" not in page:
    variance.render()

elif "Forecasting" in page and "🔒" not in page:
    forecasting.render()

elif "🔒" in page:
    st.warning("Complete the previous module to unlock this one.")

elif page == "About":
    st.title("About ControllerSim")
    st.markdown("""
Built as part of a self-directed transition into finance.

This tool covers the core skill set of a business controller:
- Financial reporting (P&L, balance sheet, cash flow)
- Budgeting (department and headcount budgets)
- Variance analysis (actuals vs. budget, CFO-ready explanations)
- Forecasting (rolling forecast updates with narrative rationale)

**Tech stack:** Python · Streamlit · Claude AI (Anthropic)

All scenarios are based on a fictional company — Nexova Ltd.
    """)
