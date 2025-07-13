"""
Frontend-Backend Integration Tests

These tests validate the complete integration between the React frontend
and FastAPI backend, including SSE communication, API endpoints, and data flow.
"""

import asyncio
import json
import time
import pytest
import sys
import os
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, patch, MagicMock

# Add the backend src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from api import router  # noqa: E402


class TestFrontendBackendIntegration:
    """Integration tests for frontend-backend communication."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with routes."""
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sse_client(self, app):
        """Create SSE test client."""
        return TestClient(app)

    def test_health_endpoint_integration(self, client):
        """Test health endpoint that frontend uses for status checks."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Verify structure expected by frontend
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

        # Verify headers for CORS
        assert response.headers.get("access-control-allow-origin") is not None

    def test_settings_endpoint_integration(self, client):
        """Test settings endpoint that frontend uses for configuration."""
        response = client.get("/settings")

        assert response.status_code == 200
        settings = response.json()

        # Verify settings structure expected by frontend
        required_fields = ["environment", "log_level", "max_sections"]
        for field in required_fields:
            assert field in settings

        # Verify reasonable values
        assert isinstance(settings["max_sections"], int)
        assert settings["max_sections"] > 0
        assert settings["max_sections"] <= 50  # Reasonable upper limit

    @pytest.mark.asyncio
    async def test_sse_endpoint_integration_with_mocks(self, client):
        """Test SSE endpoint integration with mocked agents."""
        # Create test data
        section_responses = ['{"content": "Test section", "sources": ["test.com"]}']
        assembler_response = "# Test Report\n\nComplete test report"

        with (
            patch("api.routes.SectionResearcher") as mock_researcher,
            patch("api.routes.ReportAssembler") as mock_assembler,
        ):

            # Setup mocks
            researcher_agent = AsyncMock()
            researcher_responses = [json.dumps(resp) for resp in section_responses]
            researcher_agent.run.side_effect = researcher_responses
            researcher_instance = MagicMock()
            researcher_instance.agent = researcher_agent
            mock_researcher.return_value = researcher_instance

            assembler_agent = AsyncMock()
            assembler_agent.run.return_value = assembler_response
            assembler_instance = MagicMock()
            assembler_instance.agent = assembler_agent
            mock_assembler.return_value = assembler_instance

            # Make SSE request
            with client.stream(
                "GET",
                "/sse",
                params={
                    "topic": "AI Research Integration Test",
                    "guidelines": "Academic format with sources",
                    "sections": "Introduction,Methods",
                },
            ) as response:

                assert response.status_code == 200
                assert response.headers["content-type"] == "text/plain; charset=utf-8"
                assert response.headers["cache-control"] == "no-cache"

                # Collect SSE events
                events = []
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        try:
                            event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                            events.append(event_data)
                        except json.JSONDecodeError:
                            continue

                # Verify events structure expected by frontend
                assert len(events) >= 3  # 2 sections + 1 final report

                # Check section events
                section_events = [e for e in events if e.get("type") == "section"]
                assert len(section_events) == 2

                for event in section_events:
                    assert "section" in event
                    assert "content" in event
                    assert "sources" in event
                    assert isinstance(event["sources"], list)

                # Check final report event
                report_events = [e for e in events if e.get("type") == "report"]
                assert len(report_events) == 1

                report_event = report_events[0]
                assert "content" in report_event
                assert "Introduction" in report_event["content"]
                assert "Methods" in report_event["content"]
                assert "References" in report_event["content"]

    def test_sse_parameter_validation_integration(self, client):
        """Test SSE parameter validation that frontend relies on."""
        # Test missing required parameters
        test_cases = [
            ({}, 422),  # No parameters
            ({"topic": "test"}, 422),  # Missing guidelines and sections
            ({"topic": "test", "guidelines": "test"}, 422),  # Missing sections
            ({"guidelines": "test", "sections": "intro"}, 422),  # Missing topic
            ({"topic": "", "guidelines": "test", "sections": "intro"}, 422),  # Empty topic
            ({"topic": "test", "guidelines": "", "sections": "intro"}, 422),  # Empty guidelines
            ({"topic": "test", "guidelines": "test", "sections": ""}, 422),  # Empty sections
            ({"topic": "valid", "guidelines": "valid", "sections": "Introduction"}, 200),  # Valid
        ]

        for params, expected_status in test_cases:
            response = client.get("/sse", params=params)
            assert response.status_code == expected_status, f"Failed for params: {params}"

            if expected_status == 422:
                # Verify error response structure for frontend
                error_data = response.json()
                assert "detail" in error_data

    def test_cors_integration(self, client):
        """Test CORS configuration for frontend integration."""
        # Test preflight request
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        # Should allow CORS
        assert response.status_code in [200, 204]

        # Test actual request with CORS headers
        response = client.get("/health", headers={"Origin": "http://localhost:5173"})

        assert response.status_code == 200
        cors_origin = response.headers.get("access-control-allow-origin")
        assert cors_origin in ["*", "http://localhost:5173"]

    @pytest.mark.asyncio
    async def test_concurrent_sse_connections_integration(self, client):
        """Test handling of concurrent SSE connections from multiple frontend clients."""

        async def make_sse_request(client_id):
            """Make an SSE request for a specific client."""
            with (
                patch("api.routes.SectionResearcher") as mock_researcher,
                patch("api.routes.ReportAssembler") as mock_assembler,
            ):

                # Quick mock setup
                researcher_agent = AsyncMock()
                researcher_agent.run.return_value = json.dumps(
                    {
                        "content": f"Content for client {client_id}",
                        "sources": [f"source{client_id}.com"],
                    }
                )
                researcher_instance = MagicMock()
                researcher_instance.agent = researcher_agent
                mock_researcher.return_value = researcher_instance

                assembler_agent = AsyncMock()
                assembler_agent.run.return_value = (
                    f"# Report for Client {client_id}\n\nContent here."
                )
                assembler_instance = MagicMock()
                assembler_instance.agent = assembler_agent
                mock_assembler.return_value = assembler_instance

                with client.stream(
                    "GET",
                    "/sse",
                    params={
                        "topic": f"Topic {client_id}",
                        "guidelines": f"Guidelines {client_id}",
                        "sections": "Introduction",
                    },
                ) as response:

                    assert response.status_code == 200
                    events = []

                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            try:
                                event_data = json.loads(line[6:])
                                events.append(event_data)
                                if event_data.get("type") == "report":
                                    break  # Got final report, can exit
                            except json.JSONDecodeError:
                                continue

                    return len(events)

        # Simulate 3 concurrent frontend clients
        tasks = [make_sse_request(i) for i in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All requests should complete successfully
        assert len(results) == 3
        for result in results:
            assert not isinstance(result, Exception), f"Request failed: {result}"
            assert result > 0, "Should have received events"

    def test_error_response_format_integration(self, client):
        """Test error response format that frontend expects."""
        # Test 404 error
        response = client.get("/nonexistent")
        assert response.status_code == 404

        error_data = response.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], str)

        # Test 405 error (method not allowed)
        response = client.post("/health")
        assert response.status_code == 405

        error_data = response.json()
        assert "detail" in error_data

        # Test validation error format
        response = client.get("/sse", params={"invalid": "params"})
        assert response.status_code == 422

        error_data = response.json()
        assert "detail" in error_data

        # Should be in format that frontend can handle
        if isinstance(error_data["detail"], list):
            # Pydantic validation error format
            for error in error_data["detail"]:
                assert "loc" in error
                assert "msg" in error
                assert "type" in error

    @pytest.mark.asyncio
    async def test_sse_event_format_integration(self, client):
        """Test SSE event format expected by frontend."""
        with (
            patch("api.routes.SectionResearcher") as mock_researcher,
            patch("api.routes.ReportAssembler") as mock_assembler,
        ):

            # Setup detailed mock response
            researcher_agent = AsyncMock()
            researcher_agent.run.return_value = json.dumps(
                {
                    "content": "Detailed section content with **markdown** formatting.",
                    "sources": [
                        "https://example.com/source1",
                        "https://academic.org/paper2",
                        "https://research.edu/study3",
                    ],
                }
            )
            researcher_instance = MagicMock()
            researcher_instance.agent = researcher_agent
            mock_researcher.return_value = researcher_instance

            assembler_agent = AsyncMock()
            assembler_agent.run.return_value = """# Research Report

## Table of Contents
1. Introduction

## 1. Introduction
Detailed section content with **markdown** formatting.

## References
- [1] https://example.com/source1
- [2] https://academic.org/paper2
- [3] https://research.edu/study3
"""
            assembler_instance = MagicMock()
            assembler_instance.agent = assembler_agent
            mock_assembler.return_value = assembler_instance

            with client.stream(
                "GET",
                "/sse",
                params={
                    "topic": "Event Format Test",
                    "guidelines": "Test event formatting",
                    "sections": "Introduction",
                },
            ) as response:

                events = []
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        try:
                            event_data = json.loads(line[6:])
                            events.append(event_data)
                        except json.JSONDecodeError:
                            continue

                # Verify section event format
                section_events = [e for e in events if e.get("type") == "section"]
                assert len(section_events) >= 1

                section_event = section_events[0]
                assert section_event["type"] == "section"
                assert section_event["section"] == "Introduction"
                assert "content" in section_event
                assert "sources" in section_event
                assert isinstance(section_event["sources"], list)
                assert len(section_event["sources"]) == 3

                # Verify report event format
                report_events = [e for e in events if e.get("type") == "report"]
                assert len(report_events) == 1

                report_event = report_events[0]
                assert report_event["type"] == "report"
                assert "content" in report_event
                assert report_event["content"].startswith("# Research Report")
                assert "References" in report_event["content"]

    def test_performance_integration(self, client):
        """Test performance characteristics for frontend integration."""
        # Test health check performance (frontend polls this)
        start_time = time.time()
        response = client.get("/health")
        health_response_time = time.time() - start_time

        assert response.status_code == 200
        assert health_response_time < 1.0, f"Health check too slow: {health_response_time:.2f}s"

        # Test settings endpoint performance
        start_time = time.time()
        response = client.get("/settings")
        settings_response_time = time.time() - start_time

        assert response.status_code == 200
        assert settings_response_time < 2.0, f"Settings too slow: {settings_response_time:.2f}s"

        # Test SSE connection establishment time
        start_time = time.time()

        with (
            patch("api.routes.SectionResearcher") as mock_researcher,
            patch("api.routes.ReportAssembler") as mock_assembler,
        ):

            # Quick mock
            researcher_agent = AsyncMock()
            researcher_agent.run.return_value = json.dumps({"content": "Quick test", "sources": []})
            researcher_instance = MagicMock()
            researcher_instance.agent = researcher_agent
            mock_researcher.return_value = researcher_instance

            assembler_agent = AsyncMock()
            assembler_agent.run.return_value = "# Quick Report"
            assembler_instance = MagicMock()
            assembler_instance.agent = assembler_agent
            mock_assembler.return_value = assembler_instance

            with client.stream(
                "GET",
                "/sse",
                params={
                    "topic": "Performance Test",
                    "guidelines": "Quick test",
                    "sections": "Introduction",
                },
            ) as response:

                first_event_time = None
                for line in response.iter_lines():
                    if line.startswith("data: ") and first_event_time is None:
                        first_event_time = time.time()
                        break

                if first_event_time:
                    sse_first_event_time = first_event_time - start_time
                    assert (
                        sse_first_event_time < 10.0
                    ), f"SSE first event too slow: {sse_first_event_time:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
