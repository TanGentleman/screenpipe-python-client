try:
    import pytest
except ImportError:
    raise SystemExit("Pytest is required to run the tests.")

from src.server.server import run_pipeline
from cli.app import chat_with_api


def test_full_pipeline():
    """Test the complete pipeline flow."""
    test_body = {
        "messages": [
            {"role": "user", "content": "Search: limit of 1, type all"}
        ],
        "stream": False
    }

    try:
        response = run_pipeline(test_body)
        assert response is not None
    except Exception as e:
        pytest.fail(f"Pipeline test failed: {e}")


def test_chat_pipeline():
    """Test the chat interface pipeline."""
    messages = [
        {"role": "user", "content": "Search audio from the last month, limit of 3"}
    ]

    response = chat_with_api(messages)
    assert isinstance(response, dict)
    assert "messages" in response
