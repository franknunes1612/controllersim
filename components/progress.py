import streamlit as st

MODULES = ["statements", "budgeting", "variance", "forecasting"]
SCORE_VALUES = {"pass": 1.0, "partial": 0.5, "fail": 0.0}


def empty_progress() -> dict:
    """Return a fresh progress dict with no scores."""
    return {module: {"scores": [], "completed": False} for module in MODULES}


def init_progress() -> None:
    """Initialise progress in Streamlit session state if not already present."""
    if "progress" not in st.session_state:
        st.session_state.progress = empty_progress()


def record_score(progress: dict, module: str, scenario_idx: int, signal: str) -> dict:
    """Record a scenario score. Overwrites if already scored."""
    score_value = SCORE_VALUES[signal]
    scores = progress[module]["scores"]
    if len(scores) <= scenario_idx:
        scores.append(score_value)
    else:
        scores[scenario_idx] = score_value
    return progress


def is_module_unlocked(progress: dict, module: str) -> bool:
    """Return True if the module is available to the user."""
    idx = MODULES.index(module)
    if idx == 0:
        return True
    prev_module = MODULES[idx - 1]
    return progress[prev_module]["completed"]


def mark_module_complete(progress: dict, module: str) -> dict:
    """Mark a module as completed."""
    progress[module]["completed"] = True
    return progress


def get_readiness_score(progress: dict) -> int:
    """Return overall Controller Readiness Score as an integer 0–100."""
    all_scores = []
    for module in MODULES:
        all_scores.extend(progress[module]["scores"])
    if not all_scores:
        return 0
    return int((sum(all_scores) / len(all_scores)) * 100)
