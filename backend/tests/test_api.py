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
    assert "task_id" in response.json()
    assert response.json()["message"] == "Research request received"

import pytest
from unittest.mock import AsyncMock, patch
import json

@pytest.mark.asyncio
async def test_sse_endpoint():
    with patch("src.main.research_service.conduct_research") as mock_conduct_research:
        mock_conduct_research.return_value = AsyncMock()
        mock_conduct_research.return_value.__aiter__.return_value = [
            {"event": "start", "data": {"message": "Research process initiated.", "topic": "Test Topic"}},
            {"event": "section_complete", "data": {"title": "Intro", "content_preview": "Intro content...", "sources_count": 1}},
            {"event": "report_complete", "data": {"report": "# Final Report"}},
            {"event": "end", "data": "Research process finished."},
        ]

        # Simulate submitting a research request to get a task_id
        submit_response = client.post("/research", json={
            "topic": "Test Topic",
            "guidelines": "Test Guidelines",
            "sections": "Intro"
        })
        assert submit_response.status_code == 200
        task_id = submit_response.json()["task_id"]

        with client.stream("GET", f"/sse?task_id={task_id}") as response:
            assert response.status_code == 200
            events = []
            for line in response.iter_lines():
                if line.startswith("data:"):
                    events.append(json.loads(line[len("data:"):].strip()))

            assert len(events) == 4
            assert events[0]["event"] == "start"
            assert events[1]["event"] == "section_complete"
            assert events[2]["event"] == "report_complete"
            assert events[3]["event"] == "end"

@pytest.mark.asyncio
async def test_sse_endpoint_task_not_found():
    response = client.get("/sse?task_id=non_existent_id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Task ID not found"}







