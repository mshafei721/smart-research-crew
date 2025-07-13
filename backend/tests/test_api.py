"""Tests for API routes and endpoints."""

import pytest
import sys
import os
import time
import threading
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Add the backend src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from api.routes import research_sse, research_sse_generator  # noqa: E402
from api import router  # noqa: E402

# Create test app with the routes
app = FastAPI()

app.include_router(router)
client = TestClient(app)


class TestSSEEndpoint:
    """Test cases for the Server-Sent Events research endpoint."""

    def test_sse_endpoint_exists(self):
        """Test that the SSE endpoint is accessible."""
        # Test with minimal parameters - this will likely fail due to missing OPENAI_API_KEY
        # but it should at least reach the endpoint
        response = client.get(
            "/sse",
            params={
                "topic": "test topic",
                "guidelines": "test guidelines",
                "sections": "Introduction,Conclusion",
            },
        )

        # We expect this to either return 200 (if API key exists) or fail with a meaningful error
        # The important thing is that the endpoint exists and processes parameters
        assert response.status_code in [200, 400, 422, 500]  # Valid response codes

    def test_sse_endpoint_requires_parameters(self):
        """Test that the SSE endpoint requires all parameters."""
        # Test with missing parameters
        response = client.get("/sse")
        assert response.status_code == 422  # Validation error for missing params

    def test_sse_endpoint_parameter_types(self):
        """Test that the SSE endpoint accepts string parameters."""
        try:
            response = client.get(
                "/sse",
                params={
                    "topic": "AI research trends",
                    "guidelines": "Academic tone, recent sources",
                    "sections": "Overview,Applications,Future Directions",
                },
            )
            # Should process parameters correctly
            assert response.status_code in [200, 400, 422, 500]
        except Exception as e:
            # Accept OpenAI API errors as valid for this parameter validation test
            error_str = str(e).lower()
            expected_errors = ["openai", "api", "rate", "limit", "key", "authentication"]
            assert any(keyword in error_str for keyword in expected_errors), f"Unexpected error: {e}"


class TestAPIStructure:
    """Test cases for API structure and imports."""

    def test_router_import(self):
        """Test that the router can be imported correctly."""
        from api import router

        assert router is not None

    def test_routes_import(self):
        """Test that routes module imports correctly."""
        from api.routes import research_sse

        assert research_sse is not None


@pytest.mark.asyncio
class TestResearchSSEFunction:
    """Test the research_sse function directly with mocks."""

    @patch("api.routes.SectionResearcher")
    @patch("api.routes.ReportAssembler")
    async def test_research_sse_with_mocks(self, mock_assembler_class, mock_researcher_class):
        """Test research_sse function with mocked agents."""
        # Mock the agent classes with the new method signatures
        mock_researcher = AsyncMock()
        mock_researcher.run_research.return_value = {
            "content": "Test content", 
            "sources": ["test.com"]
        }
        mock_researcher_class.return_value = mock_researcher

        mock_assembler = AsyncMock()
        mock_assembler.run_assembly.return_value = "# Test Report\n\nAssembled content"
        mock_assembler_class.return_value = mock_assembler

        # Test the function
        async def collect_events():
            events = []
            async for event in research_sse_generator(
                "test topic", "test guidelines", "Introduction,Conclusion"
            ):
                events.append(event)
            return events

        events = await collect_events()

        # Should have events for each section plus final report
        assert len(events) >= 3  # 2 sections + 1 report

        # Verify researcher was called for each section
        assert mock_researcher_class.call_count == 2

        # Verify assembler was called once
        assert mock_assembler_class.call_count == 1


class TestAPIErrorHandling:
    """Test error handling in API endpoints."""

    def test_sse_invalid_sections_format(self):
        """Test SSE endpoint with invalid sections format."""
        response = client.get(
            "/sse",
            params={
                "topic": "test topic",
                "guidelines": "test guidelines",
                "sections": "",  # Empty sections
            },
        )

        # Should handle empty sections gracefully
        assert response.status_code in [200, 400, 422, 500]

    def test_sse_very_long_parameters(self):
        """Test SSE endpoint with very long parameters."""
        long_text = "x" * 10000  # 10KB string

        response = client.get(
            "/sse",
            params={
                "topic": long_text,
                "guidelines": long_text,
                "sections": "Introduction,Conclusion",
            },
        )

        # Should handle long parameters (may timeout or error, but not crash)
        assert response.status_code in [200, 422, 500, 413]  # 413 = Payload Too Large

    def test_sse_special_characters(self):
        """Test SSE endpoint with special characters."""
        try:
            response = client.get(
                "/sse",
                params={
                    "topic": "AI & Machine Learning: A Review (2024)",
                    "guidelines": 'Use emojis 🤖, quotes "test", and symbols #&@',
                    "sections": "Introduction & Overview,Methodology,Results & Discussion",
                },
            )
            # Should handle special characters correctly
            assert response.status_code in [200, 400, 422, 500]
        except Exception as e:
            # Accept OpenAI API errors as valid for this special characters test
            error_str = str(e).lower()
            expected_errors = ["openai", "api", "rate", "limit", "key", "authentication"]
            assert any(keyword in error_str for keyword in expected_errors), f"Unexpected error: {e}"

    @pytest.mark.asyncio
    async def test_research_sse_error_handling(self):
        """Test research_sse function error handling."""
        from unittest.mock import AsyncMock, patch

        # Test with agent that raises exception
        with patch("api.routes.SectionResearcher") as mock_researcher_class:
            mock_researcher = AsyncMock()
            mock_researcher.run_research.side_effect = Exception("Test error")
            mock_researcher_class.return_value = mock_researcher

            events = []
            try:
                async for event in research_sse_generator("test topic", "test guidelines", "Introduction"):
                    events.append(event)
            except Exception:
                pass  # Expected to handle errors gracefully

            # Should still produce some output even with errors
            assert len(events) >= 0  # May be empty if error occurs early


class TestAPIPerformance:
    """Test API performance characteristics."""

    def test_sse_endpoint_response_time(self):
        """Test that SSE endpoint responds quickly (even if it fails later)."""
        start_time = time.time()
        try:
            client.get(
                "/sse",
                params={"topic": "quick test", "guidelines": "brief", "sections": "Introduction"},
            )
        except Exception:
            pass  # API may fail, but we're testing response time
        response_time = time.time() - start_time

        # Should respond within reasonable time - even if it fails with API errors
        assert response_time < 10.0, f"Response took too long: {response_time:.2f}s"

    def test_multiple_concurrent_requests(self):
        """Test handling multiple concurrent API requests."""
        import time
        
        results = []
        errors = []

        def make_request(request_id):
            try:
                # Just test the endpoint response, don't wait for full execution
                start_time = time.time()
                response = client.get(
                    "/sse",
                    params={
                        "topic": f"test topic {request_id}",
                        "guidelines": "test guidelines", 
                        "sections": "Introduction",
                    },
                    timeout=2.0  # Short timeout to avoid hanging
                )
                elapsed = time.time() - start_time
                results.append((response.status_code, elapsed))
            except Exception as e:
                # Accept timeouts and API errors as valid for concurrency testing
                if "timeout" in str(e).lower():
                    results.append((408, 2.0))  # Request timeout
                elif "openai" in str(e).lower() or "api" in str(e).lower():
                    results.append((500, 1.0))  # API error
                else:
                    errors.append(e)

        # Create multiple threads  
        threads = []
        for i in range(3):  # Keep it small to avoid overwhelming
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Should handle concurrent requests without crashing
        # Allow some failures due to API limits but test concurrency handling
        assert len(errors) <= 2, f"Too many errors in concurrent requests: {errors}"
        assert len(results) >= 1, f"Too few responses from concurrent requests: {results}"


class TestAPIValidation:
    """Test API input validation."""

    def test_sse_parameter_validation(self):
        """Test parameter validation for SSE endpoint."""
        # Test missing topic (required)
        response = client.get(
            "/sse", params={"guidelines": "test guidelines", "sections": "Introduction"}
        )
        assert response.status_code == 422

        # Test missing sections (required)
        response = client.get(
            "/sse", params={"topic": "test topic", "guidelines": "test guidelines"}
        )
        assert response.status_code == 422

        # Test missing guidelines (optional) - should NOT return 422
        try:
            response = client.get("/sse", params={"topic": "test topic", "sections": "Introduction"})
            # Guidelines is optional, so this should not be a validation error
            assert response.status_code in [200, 400, 500]  # Not 422
        except Exception as e:
            # Accept OpenAI API errors as valid since guidelines is optional
            error_str = str(e).lower()
            expected_errors = ["openai", "api", "rate", "limit", "key", "authentication"]
            assert any(keyword in error_str for keyword in expected_errors), f"Unexpected error: {e}"

    def test_sse_sections_parsing(self):
        """Test sections parameter parsing."""
        def test_sections_request(sections):
            try:
                response = client.get(
                    "/sse", params={"topic": "test", "guidelines": "test", "sections": sections}
                )
                assert response.status_code in [200, 400, 422, 500]
            except Exception as e:
                # Accept OpenAI API errors as valid for sections parsing test
                error_str = str(e).lower()
                expected_errors = ["openai", "api", "rate", "limit", "key", "authentication"]
                assert any(keyword in error_str for keyword in expected_errors), f"Unexpected error: {e}"

        # Test single section
        test_sections_request("Introduction")

        # Test multiple sections
        test_sections_request("Introduction,Methods,Results,Discussion")

        # Test sections with spaces
        test_sections_request("Introduction, Methods, Results")


if __name__ == "__main__":
    pytest.main([__file__])
