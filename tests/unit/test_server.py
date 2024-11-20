import pytest
from fastapi.testclient import TestClient
from server import app, Models
from utils.owui_utils.pipeline_utils import get_inlet_body

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

def test_update_valves():
    """Test valve configuration updates."""
    test_config = {
        "filter_config": {
            "NATIVE_TOOL_CALLING": True,
            "TOOL_MODEL": Models.SMART_MODEL
        },
        "pipe_config": {
            "RESPONSE_MODEL": Models.FLASH_MODEL
        }
    }
    response = client.post("/valves/update", json=test_config)
    assert response.status_code == 200
    assert "message" in response.json() 