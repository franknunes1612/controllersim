import json
import pytest
from unittest.mock import MagicMock, patch
from components.feedback import get_ai_feedback, grade_questions, grade_table_input


# --- grade_questions (pure, no mock needed) ---

def test_grade_questions_all_correct_number():
    questions = [{"id": "q1", "type": "number", "text": "Gross margin?", "unit": "%", "correct_answer": 70, "tolerance": 1}]
    signal, feedback = grade_questions(questions, {"q1": 70})
    assert signal == "pass"


def test_grade_questions_number_within_tolerance():
    questions = [{"id": "q1", "type": "number", "text": "Gross margin?", "unit": "%", "correct_answer": 70, "tolerance": 1}]
    signal, feedback = grade_questions(questions, {"q1": 71})
    assert signal == "pass"


def test_grade_questions_number_out_of_tolerance():
    questions = [{"id": "q1", "type": "number", "text": "Gross margin?", "unit": "%", "correct_answer": 70, "tolerance": 1}]
    signal, feedback = grade_questions(questions, {"q1": 60})
    assert signal == "fail"


def test_grade_questions_multiple_choice_correct():
    questions = [{"id": "q1", "type": "multiple_choice", "text": "Largest expense?", "options": ["A", "B"], "correct_answer": "A"}]
    signal, feedback = grade_questions(questions, {"q1": "A"})
    assert signal == "pass"


def test_grade_questions_multiple_choice_wrong():
    questions = [{"id": "q1", "type": "multiple_choice", "text": "Largest expense?", "options": ["A", "B"], "correct_answer": "A"}]
    signal, feedback = grade_questions(questions, {"q1": "B"})
    assert signal == "fail"


def test_grade_questions_partial_score():
    questions = [
        {"id": "q1", "type": "number", "text": "Q1?", "unit": "%", "correct_answer": 70, "tolerance": 1},
        {"id": "q2", "type": "number", "text": "Q2?", "unit": "%", "correct_answer": 17, "tolerance": 1},
    ]
    signal, feedback = grade_questions(questions, {"q1": 70, "q2": 99})
    assert signal == "partial"


# --- grade_table_input (pure, no mock needed) ---

def test_grade_table_input_all_correct():
    fields = [{"id": "f1", "label": "Personnel (€)", "correct_answer": 165000, "tolerance_pct": 0}]
    signal, feedback = grade_table_input(fields, {"f1": 165000})
    assert signal == "pass"


def test_grade_table_input_wrong():
    fields = [{"id": "f1", "label": "Personnel (€)", "correct_answer": 165000, "tolerance_pct": 0}]
    signal, feedback = grade_table_input(fields, {"f1": 100000})
    assert signal == "fail"


# --- get_ai_feedback (mocked Anthropic) ---

def _mock_anthropic_response(json_str: str):
    mock_content = MagicMock()
    mock_content.text = json_str
    mock_message = MagicMock()
    mock_message.content = [mock_content]
    return mock_message


def test_get_ai_feedback_returns_parsed_dict():
    scenario = {
        "prompt": "Explain the variance.",
        "rubric": ["Identifies unfavourable variance", "Quantifies the gap"],
        "model_answer": "The variance was €13,500 unfavourable.",
    }
    response_json = json.dumps({
        "signal": "pass",
        "feedback": "Great explanation.",
        "tip": "Always lead with the number.",
    })

    with patch("components.feedback.anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = _mock_anthropic_response(response_json)

        result = get_ai_feedback(scenario, "The marketing variance was €13,500 unfavourable.")

    assert result["signal"] == "pass"
    assert "feedback" in result
    assert "tip" in result


def test_get_ai_feedback_fallback_on_bad_json():
    scenario = {
        "prompt": "Explain the variance.",
        "rubric": ["Point A"],
        "model_answer": "Model answer.",
    }

    with patch("components.feedback.anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = _mock_anthropic_response("not valid json {{")

        result = get_ai_feedback(scenario, "Some answer.")

    assert result["signal"] == "partial"
    assert "feedback" in result
    assert "tip" in result
