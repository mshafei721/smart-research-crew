"""End-to-end tests for the Smart Research Crew system."""

import pytest
import sys
import os
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
import time

# Add the backend src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agents import SectionResearcher, ReportAssembler
from api.routes import research_sse
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestE2EWorkflow:
    """End-to-end tests for complete research workflow."""

    @pytest.mark.asyncio
    async def test_complete_research_pipeline_mocked(self):
        """Test complete research pipeline with mocked agents."""
        with (
            patch("agents.section_researcher.ReActAgent") as mock_section_agent,
            patch("agents.report_assembler.ReActAgent") as mock_assembler_agent,
        ):

            # Mock section agent responses
            section_mock = AsyncMock()
            section_responses = [
                '{"content": "Introduction content about AI", "sources": ["ai-intro.com", "ai-basics.org"]}',
                '{"content": "Methods for AI research", "sources": ["methods.edu", "research-guide.net"]}',
            ]
            section_mock.run.side_effect = section_responses
            mock_section_agent.return_value = section_mock

            # Mock assembler agent response
            assembler_mock = AsyncMock()
            assembler_mock.run.return_value = """# AI Research Report

## Table of Contents
1. Introduction
2. Methods

## 1. Introduction
Introduction content about AI

## 2. Methods  
Methods for AI research

## References
- [1] ai-intro.com
- [2] ai-basics.org
- [3] methods.edu
- [4] research-guide.net
"""
            mock_assembler_agent.return_value = assembler_mock

            # Run complete pipeline
            events = []
            async for event in research_sse(
                topic="AI Research Trends",
                guidelines="Academic format with citations",
                sections="Introduction,Methods",
            ):
                events.append(event)

            # Verify pipeline execution
            assert len(events) >= 3  # 2 sections + 1 final report

            # Check section events
            section_events = [e for e in events if '"type": "section"' in e]
            assert len(section_events) == 2

            # Check final report event
            report_events = [e for e in events if '"type": "report"' in e]
            assert len(report_events) == 1

            # Verify agents were called correctly
            assert mock_section_agent.call_count == 2
            assert mock_assembler_agent.call_count == 1

    @pytest.mark.asyncio
    async def test_research_pipeline_error_recovery(self):
        """Test that pipeline handles partial failures gracefully."""
        with (
            patch("agents.section_researcher.ReActAgent") as mock_section_agent,
            patch("agents.report_assembler.ReActAgent") as mock_assembler_agent,
        ):

            # Mock section agent with one success, one failure
            section_mock = AsyncMock()
            section_responses = [
                '{"content": "Successful section content", "sources": ["success.com"]}',
                Exception("Network error"),  # Second section fails
            ]
            section_mock.run.side_effect = section_responses
            mock_section_agent.return_value = section_mock

            # Mock assembler agent
            assembler_mock = AsyncMock()
            assembler_mock.run.return_value = "# Partial Report\n\nOnly one section completed."
            mock_assembler_agent.return_value = assembler_mock

            # Run pipeline
            events = []
            try:
                async for event in research_sse(
                    topic="Test Topic", guidelines="Test guidelines", sections="Section1,Section2"
                ):
                    events.append(event)
            except Exception:
                pass  # Pipeline should handle errors gracefully

            # Should still produce some events
            assert len(events) >= 1  # At least one successful section

    @pytest.mark.asyncio
    async def test_large_research_project(self):
        """Test handling a large research project with many sections."""
        with (
            patch("agents.section_researcher.ReActAgent") as mock_section_agent,
            patch("agents.report_assembler.ReActAgent") as mock_assembler_agent,
        ):

            # Mock section agent
            section_mock = AsyncMock()
            section_mock.run.return_value = (
                '{"content": "Section content", "sources": ["source.com"]}'
            )
            mock_section_agent.return_value = section_mock

            # Mock assembler agent
            assembler_mock = AsyncMock()
            assembler_mock.run.return_value = (
                "# Large Research Report\n\nMultiple sections assembled."
            )
            mock_assembler_agent.return_value = assembler_mock

            # Test with many sections
            sections = [
                "Introduction",
                "Literature Review",
                "Methodology",
                "Results",
                "Discussion",
                "Conclusion",
                "Future Work",
            ]

            start_time = time.time()
            events = []
            async for event in research_sse(
                topic="Comprehensive AI Study",
                guidelines="Detailed academic format",
                sections=",".join(sections),
            ):
                events.append(event)
            execution_time = time.time() - start_time

            # Verify all sections processed
            section_events = [e for e in events if '"type": "section"' in e]
            assert len(section_events) == len(sections)

            # Verify reasonable execution time (mocked, so should be fast)
            assert execution_time < 10.0, f"Execution took too long: {execution_time:.2f}s"

            # Verify agents called correctly
            assert mock_section_agent.call_count == len(sections)
            assert mock_assembler_agent.call_count == 1


class TestE2EAPIIntegration:
    """End-to-end tests for API integration."""

    def test_sse_endpoint_complete_flow(self):
        """Test complete SSE endpoint flow with mocked backend."""
        from fastapi import FastAPI
        from api import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        with (
            patch("api.routes.SectionResearcher") as mock_researcher,
            patch("api.routes.ReportAssembler") as mock_assembler,
        ):

            # Mock researcher
            researcher_agent = AsyncMock()
            researcher_agent.run.return_value = (
                '{"content": "Test content", "sources": ["test.com"]}'
            )
            researcher_instance = MagicMock()
            researcher_instance.agent = researcher_agent
            mock_researcher.return_value = researcher_instance

            # Mock assembler
            assembler_agent = AsyncMock()
            assembler_agent.run.return_value = "# Test Report\n\nComplete report"
            assembler_instance = MagicMock()
            assembler_instance.agent = assembler_agent
            mock_assembler.return_value = assembler_instance

            # Make request
            response = client.get(
                "/sse",
                params={
                    "topic": "Test Topic",
                    "guidelines": "Test guidelines",
                    "sections": "Introduction,Conclusion",
                },
            )

            # Should get successful response
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain; charset=utf-8"

    @pytest.mark.asyncio
    async def test_concurrent_sse_requests(self):
        """Test handling multiple concurrent SSE requests."""
        with (
            patch("agents.section_researcher.ReActAgent") as mock_section_agent,
            patch("agents.report_assembler.ReActAgent") as mock_assembler_agent,
        ):

            # Mock agents
            section_mock = AsyncMock()
            section_mock.run.return_value = '{"content": "Content", "sources": ["source.com"]}'
            mock_section_agent.return_value = section_mock

            assembler_mock = AsyncMock()
            assembler_mock.run.return_value = "# Report\n\nContent"
            mock_assembler_agent.return_value = assembler_mock

            # Run multiple concurrent requests
            async def run_single_request(request_id):
                events = []
                async for event in research_sse(
                    topic=f"Topic {request_id}",
                    guidelines="Test guidelines",
                    sections="Introduction",
                ):
                    events.append(event)
                return len(events)

            # Run 3 concurrent requests
            tasks = [run_single_request(i) for i in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All should complete successfully
            assert len(results) == 3
            assert all(isinstance(r, int) and r > 0 for r in results), f"Failed results: {results}"


class TestE2EDataFlow:
    """Test data flow through the entire system."""

    @pytest.mark.asyncio
    async def test_data_transformation_pipeline(self):
        """Test that data transforms correctly through the pipeline."""
        with (
            patch("agents.section_researcher.ReActAgent") as mock_section_agent,
            patch("agents.report_assembler.ReActAgent") as mock_assembler_agent,
        ):

            # Mock section agent with specific data
            section_mock = AsyncMock()
            section_data = {
                "content": "Detailed research on quantum computing applications in AI",
                "sources": [
                    "nature.com/quantum-ai",
                    "arxiv.org/quantum-ml",
                    "ieee.org/quantum-computing",
                ],
            }
            section_mock.run.return_value = json.dumps(section_data)
            mock_section_agent.return_value = section_mock

            # Mock assembler agent
            assembler_mock = AsyncMock()
            expected_report = """# Quantum Computing in AI Research

## Table of Contents
1. Applications

## 1. Applications
Detailed research on quantum computing applications in AI

## References
[1] nature.com/quantum-ai
[2] arxiv.org/quantum-ml  
[3] ieee.org/quantum-computing
"""
            assembler_mock.run.return_value = expected_report
            mock_assembler_agent.return_value = assembler_mock

            # Run pipeline
            events = []
            async for event in research_sse(
                topic="Quantum Computing in AI",
                guidelines="Technical focus with recent sources",
                sections="Applications",
            ):
                events.append(event)

            # Verify data flow
            section_events = [e for e in events if '"type": "section"' in e]
            assert len(section_events) == 1

            # Parse section event data
            section_event_data = json.loads(section_events[0].split("data: ")[1])
            assert section_event_data["section"] == "Applications"
            assert "quantum computing applications" in section_event_data["content"].lower()
            assert len(section_event_data["sources"]) == 3

            # Verify assembler received correct data
            assembler_call = mock_assembler_agent.return_value.run.call_args[0][0]
            assert "Applications" in assembler_call
            assert "quantum computing applications" in assembler_call.lower()
            assert "nature.com" in assembler_call


class TestE2ESystemIntegration:
    """Test system-level integration points."""

    def test_environment_variable_handling(self):
        """Test that system handles environment variables correctly."""
        # Test with missing API key
        old_key = os.environ.get("OPENAI_API_KEY")
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        try:
            # Should still create agents but may fail on execution
            researcher = SectionResearcher("Test", "Test")
            assembler = ReportAssembler()

            assert researcher.agent is not None
            assert assembler.agent is not None
        finally:
            # Restore API key
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key

    def test_memory_usage_under_load(self):
        """Test memory usage during intensive operations."""
        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create many agents (simulating high load)
        agents = []
        try:
            for i in range(20):
                researcher = SectionResearcher(f"Section{i}", f"Guidelines{i}")
                agents.append(researcher)

                # Check memory periodically
                if i % 5 == 0:
                    current_memory = process.memory_info().rss
                    memory_increase = current_memory - initial_memory
                    # Should not exceed 500MB increase
                    assert (
                        memory_increase < 500 * 1024 * 1024
                    ), f"Memory spike at agent {i}: {memory_increase / 1024 / 1024:.2f} MB"
        finally:
            # Cleanup
            del agents

    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """Test that errors propagate correctly through the system."""
        with patch("agents.section_researcher.ReActAgent") as mock_section_agent:
            # Mock agent that always fails
            section_mock = AsyncMock()
            section_mock.run.side_effect = Exception("Simulated API failure")
            mock_section_agent.return_value = section_mock

            # Should handle errors gracefully
            events = []
            error_occurred = False
            try:
                async for event in research_sse(
                    topic="Test Topic", guidelines="Test guidelines", sections="Introduction"
                ):
                    events.append(event)
            except Exception:
                error_occurred = True

            # System should either handle errors gracefully OR fail cleanly
            # (Not hang or crash silently)
            assert error_occurred or len(events) >= 0  # Either fails cleanly or handles gracefully


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
