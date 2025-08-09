import goal_engine


def test_form_goal_information_request():
    perception = {
        "query_type": "information_request: comparison",
        "primary_intent": "Learn",
        "complexity": "Высокая / Многошаговая",
        "urgency": "Высокая",
        "core_task": {"action": "compare", "object": "apples"},
    }
    result = goal_engine.form_goal(perception, {}, {})
    assert result["concept"] == "answer_information_request:comparison"
    assert result["priority"] == "critical"
    assert result["details"]["topic"] == "apples"
    assert isinstance(result["goal_id"], str) and result["goal_id"]
