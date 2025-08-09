import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils import _extract_json_from_response


def test_extract_json_from_code_block():
    text = "some prefix ```json {\"a\": 1} ``` some suffix"
    assert _extract_json_from_response(text) == '{"a": 1}'


def test_extract_json_simple():
    text = "random text {\"b\": 2} trailing"
    assert _extract_json_from_response(text) == '{"b": 2}'


def test_extract_json_nested():
    text = "start {\"a\": {\"b\": 3}} end"
    assert _extract_json_from_response(text) == '{"a": {"b": 3}}'


def test_extract_json_missing_braces():
    text = "no braces here"
    assert _extract_json_from_response(text) is None


def test_extract_json_unclosed():
    text = "start {\"a\": 1"
    assert _extract_json_from_response(text) is None

