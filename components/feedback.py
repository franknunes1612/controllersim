import json
import os
import anthropic
import streamlit as st


def _get_api_key() -> str:
    """Return API key from Streamlit secrets (production) or env var (local)."""
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("ANTHROPIC_API_KEY", "")


def get_ai_feedback(scenario: dict, user_answer: str) -> dict:
    """Send scenario + user answer to Claude. Return signal, feedback, tip."""
    client = anthropic.Anthropic(api_key=_get_api_key())
    rubric_str = "\n".join(f"- {point}" for point in scenario["rubric"])

    prompt = f"""You are a finance mentor grading a business controller exercise. Be encouraging but precise.

Scenario prompt given to the student:
{scenario["prompt"]}

Rubric — key points the answer must cover:
{rubric_str}

Student's answer:
{user_answer}

Respond ONLY with valid JSON in this exact format:
{{
  "signal": "pass" or "partial" or "fail",
  "feedback": "2-4 sentences referencing the student's specific answer",
  "tip": "one concrete improvement suggestion"
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(message.content[0].text)
    except Exception:
        return {
            "signal": "partial",
            "feedback": "Your answer was received but could not be fully evaluated. Please try again.",
            "tip": "Make sure your answer is clear and specific.",
        }


def grade_questions(questions: list, answers: dict) -> tuple:
    """Grade multiple-choice and number questions. Returns (signal, feedback)."""
    correct = 0
    wrong = []
    for q in questions:
        answer = answers.get(q["id"])
        if q["type"] == "number":
            if answer is not None and abs(float(answer) - q["correct_answer"]) <= q.get("tolerance", 0):
                correct += 1
            else:
                wrong.append(f"{q['text']} (correct: {q['correct_answer']}{q.get('unit','')})")
        elif q["type"] == "multiple_choice":
            if answer == q["correct_answer"]:
                correct += 1
            else:
                wrong.append(f"{q['text']} (correct: {q['correct_answer']})")

    total = len(questions)
    ratio = correct / total if total > 0 else 0

    if ratio == 1.0:
        return "pass", f"All {total} questions correct. Well done."
    elif ratio >= 0.5:
        return "partial", f"{correct}/{total} correct. Review: " + " | ".join(wrong)
    else:
        return "fail", f"{correct}/{total} correct. Review: " + " | ".join(wrong)


def grade_table_input(fields: list, answers: dict) -> tuple:
    """Grade budget table inputs. Returns (signal, feedback)."""
    correct = 0
    wrong = []
    for field in fields:
        answer = answers.get(field["id"], 0) or 0
        tolerance = field.get("tolerance_pct", 0) / 100 * field["correct_answer"]
        if abs(float(answer) - field["correct_answer"]) <= max(tolerance, 0.5):
            correct += 1
        else:
            wrong.append(f"{field['label']} (correct: €{field['correct_answer']:,})")

    total = len(fields)
    ratio = correct / total if total > 0 else 0

    if ratio == 1.0:
        return "pass", f"All {total} fields correct."
    elif ratio >= 0.5:
        return "partial", f"{correct}/{total} correct. Review: " + " | ".join(wrong)
    else:
        return "fail", f"{correct}/{total} correct. Review: " + " | ".join(wrong)
