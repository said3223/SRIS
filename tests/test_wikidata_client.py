import builtins
from unittest.mock import patch, Mock
import pytest

from wikidata_client import query_wikidata, format_wikidata_entity_data


def test_query_wikidata_parses_response():
    fake_json = {
        "results": {
            "bindings": [
                {
                    "item": {"value": "Q1"},
                    "itemLabel": {"value": "Label"},
                    "lang": {"value": "en"}
                }
            ]
        }
    }
    mock_resp = Mock()
    mock_resp.json.return_value = fake_json
    mock_resp.raise_for_status = Mock()

    with patch('requests.get', return_value=mock_resp) as mock_get:
        res = query_wikidata("SELECT * WHERE {}")
        mock_get.assert_called_once()

    assert res == [{"item": "Q1", "itemLabel": "Label", "lang": "en"}]


def test_format_wikidata_entity_data():
    sample_results = [
        {
            "lang": "ru",
            "itemLabel": "ИИ",
            "itemDescription": "описание",
            "itemAltLabel": "искусственный интеллект",
            "instanceOfLabel": "концепция",
            "instanceOf": "Q1234",
            "subclassOfLabel": "технология",
            "subclassOf": "Q5678",
        },
        {
            "lang": "en",
            "itemLabel": "AI",
            "itemDescription": "description",
            "itemAltLabel": "artificial intelligence",
            "instanceOfLabel": "concept",
            "instanceOf": "Q1234",
            "subclassOfLabel": "technology",
            "subclassOf": "Q5678",
        },
    ]
    formatted = format_wikidata_entity_data("Q1", sample_results)

    assert "Концепция (RU): ИИ (QID: Q1)" in formatted["ru"]
    assert "Описание: описание" in formatted["ru"]
    assert "Концепция (EN): AI (QID: Q1)" in formatted["en"]
