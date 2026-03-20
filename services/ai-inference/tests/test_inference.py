"""
Unit tests for the AI Inference service with mocked Gemini API calls.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Patch genai.configure and GenerativeModel before importing app
with patch("google.generativeai.configure"), patch(
    "google.generativeai.GenerativeModel"
):
    from src.main import app, settings

client = TestClient(app)

settings.gemini_api_key = "fake-key-for-tests"


def _make_mock_response(text: str) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.text = text
    return mock_resp


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@patch("src.main._get_model")
def test_simplify_text(mock_get_model):
    mock_model = MagicMock()
    mock_model.generate_content.return_value = _make_mock_response(
        "This is the easy version of the text."
    )
    mock_get_model.return_value = mock_model

    response = client.post(
        "/simplify",
        json={"text": "Photosynthesis is the process by which plants convert light.", "level": "easy"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "simplified_text" in data
    assert data["level"] == "easy"
    assert data["simplified_text"] == "This is the easy version of the text."


@patch("src.main._get_model")
def test_simplify_text_medium(mock_get_model):
    mock_model = MagicMock()
    mock_model.generate_content.return_value = _make_mock_response("Medium simplified.")
    mock_get_model.return_value = mock_model

    response = client.post(
        "/simplify",
        json={"text": "Complex paragraph here.", "level": "medium"},
    )
    assert response.status_code == 200
    assert response.json()["level"] == "medium"


def test_simplify_invalid_level():
    response = client.post(
        "/simplify",
        json={"text": "Some text", "level": "beginner"},
    )
    assert response.status_code == 422


@patch("src.main._get_model")
def test_summarize_video(mock_get_model):
    summary_data = {
        "big_idea": "Photosynthesis turns sunlight into food.",
        "key_points": ["Plants use sunlight", "CO2 is consumed", "Oxygen is released"],
        "glossary": {"photosynthesis": "the process plants use to make food from light"},
        "quiz": [
            {
                "question": "What do plants use for energy?",
                "options": ["A) Sunlight", "B) Water", "C) Soil"],
                "answer": "A",
            }
        ],
    }
    mock_model = MagicMock()
    mock_model.generate_content.return_value = _make_mock_response(json.dumps(summary_data))
    mock_get_model.return_value = mock_model

    response = client.post(
        "/summarize-video",
        json={"transcript": "Today we learned about photosynthesis..."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["big_idea"] == "Photosynthesis turns sunlight into food."
    assert len(data["key_points"]) == 3
    assert "photosynthesis" in data["glossary"]


@patch("src.main._get_model")
def test_generate_visual_aid(mock_get_model):
    visual_data = {
        "concept": "Gravity",
        "emoji": "🍎",
        "one_line_definition": "The force that pulls objects toward each other",
        "colour": "#a8c5da",
        "branches": [
            {
                "label": "Mass",
                "emoji": "⚖️",
                "description": "Heavier objects have stronger gravity.",
                "examples": ["The Earth pulling the Moon", "A ball falling"],
                "colour": "#c4dfe6",
            }
        ],
        "memory_tip": "Think of an apple falling on Newton's head.",
        "real_world_connection": "Gravity keeps you on the ground when you jump.",
    }
    mock_model = MagicMock()
    mock_model.generate_content.return_value = _make_mock_response(json.dumps(visual_data))
    mock_get_model.return_value = mock_model

    response = client.post("/generate-visual-aid", json={"concept": "Gravity"})
    assert response.status_code == 200
    data = response.json()
    assert data["concept"] == "Gravity"
    assert data["emoji"] == "🍎"
    assert len(data["branches"]) == 1
