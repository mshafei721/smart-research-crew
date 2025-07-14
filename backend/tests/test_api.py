from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data

def test_get_app_settings():
    response = client.get("/settings")
    assert response.status_code == 200
    data = response.json()
    assert "llm_model" in data
    assert "max_concurrent_tasks" in data
    assert "cache_enabled" in data

def test_submit_research_request():
    data = {
        "topic": "Test Topic",
        "guidelines": "Test Guidelines",
        "sections": "Intro,Conclusion"
    }
    response = client.post("/research", json=data)
    assert response.status_code == 200
    assert response.json() == {"message": "Research request received", "topic": "Test Topic"}

import pytest

@pytest.mark.asyncio
async def test_sse_endpoint():
    with client.stream("GET", "/sse") as response:
        assert response.status_code == 200
        events = []
        for line in response.iter_lines():
            if line.startswith("event:"):
                event_name = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                event_data = line.split(":", 1)[1].strip()
                events.append({"event": event_name, "data": event_data})
            elif line == "":
                event_name = None

        assert len(events) == 4
        assert events[0] == {"event": "connected", "data": "Connection established"}
        assert events[1] == {"event": "message", "data": "Processing research request..."}
        assert events[2] == {"event": "message", "data": "Research complete!"}
        assert events[3] == {"event": "end", "data": "Stream closed"}

def test_validation_error_handling():
    invalid_data = {
        "topic": "",  # Invalid: too short
        "guidelines": "",
        "sections": ""
    }
    response = client.post("/research", json=invalid_data)
    assert response.status_code == 422
    assert "detail" in response.json()
    assert "body" in response.json()
    assert response.json()["detail"][0]["loc"] == ["body", "topic"]



def test_validation_error_handling():
    invalid_data = {
        "topic": "",  # Invalid: too short
        "guidelines": "",
        "sections": ""
    }
    response = client.post("/research", json=invalid_data)
    assert response.status_code == 422
    assert "detail" in response.json()
    assert "body" in response.json()
    assert response.json()["detail"][0]["loc"] == ["body", "topic"]

