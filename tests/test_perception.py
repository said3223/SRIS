import pytest

import perception_analysis


def test_analyze_perception_empty():
    result = perception_analysis.analyze_perception("")
    assert result["error"] == "Пустой ввод"


def test_analyze_perception_basic(monkeypatch):
    def mock_execute_llm_query(**kwargs):
        return {
            "query_type": "information_request: definition",
            "core_task": {"action": "define", "object": "SRIS"},
            "summary": "Test summary",
        }

    monkeypatch.setattr(perception_analysis, "execute_llm_query", mock_execute_llm_query)
    text = "Hello world"
    result = perception_analysis.analyze_perception(text)
    assert result["query_type"] == "information_request: definition"
    assert result["language_detected"] == "en"
    assert result["word_count"] == 2
