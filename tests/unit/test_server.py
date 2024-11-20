import json
from fastapi.testclient import TestClient
from src.server.server import app, Models
from src.utils.owui_utils.pipeline_utils import get_inlet_body, get_pipe_body

client = TestClient(app)


def test_root_endpoint():
    """Test the health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_filter_inlet():
    """Test the filter inlet endpoint."""
    test_body = get_inlet_body()
    response = client.post("/filter/inlet", json=test_body)
    assert response.status_code == 200
    # Add more specific assertions based on expected response
    # response_json = response.json()
    # # save to file
    # with open("test_filter_inlet.json", "w") as f:
    #     json.dump(response_json, f)


def test_pipe_completion():
    """Test the pipe completion endpoint."""
    test_body = get_pipe_body()
    response = client.post("/pipe/completion", json=test_body)
    assert response.status_code == 200
    response_json = response.json()
    assert "response_string" in response_json


def test_pipe_stream():
    """Test the pipe stream endpoint."""
    test_body = get_pipe_body()
    response = client.post("/pipe/stream", json=test_body)
    assert response.status_code == 200

def test_update_valves():
    """Test valve configuration updates."""
    test_config = {
        "filter_config": {
            "FORCE_TOOL_CALLING": True,
        },
        "pipe_config": {
            "RESPONSE_MODEL": Models.FLASH_MODEL
        }
    }
    response = client.post("/valves/update", json=test_config)
    assert response.status_code == 200
    assert "message" in response.json()


def test_refresh_valves():
    """Test valve configuration refresh."""
    response = client.get("/valves/refresh")
    assert response.status_code == 200
    assert "message" in response.json()
