import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils import _extract_json_from_response


def test_extract_from_json_block():
    text = "Some text\n```json\n{\"key\": 123}\n```\nMore text"
    assert _extract_json_from_response(text) == '{"key": 123}'


def test_extract_json_with_noise():
    text = "Noise before {\"a\": 1, \"b\": 2} trailing noise"
    assert _extract_json_from_response(text) == '{"a": 1, "b": 2}'
