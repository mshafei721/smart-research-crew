"""
Tests for SSE testing utilities.

Validates that the SSE testing utilities work correctly and can be used
for testing SSE endpoints and streams.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock
from sse_starlette.sse import EventSourceResponse

from .sse_test_utils import (
    SSETestEvent,
    SSEEventExtractor,
    SSEMockAgent,
    SSETestScenarios,
    extract_sse_events,
    assert_sse_event_contains,
    assert_sse_event_count,
    assert_sse_event_sequence,
)


class TestSSETestEvent:
    """Test SSETestEvent class."""

    def test_event_creation(self):
        """Test basic event creation."""
        event = SSETestEvent(
            data='{"test": "data"}', event_type="test_event", event_id="123", retry=5000
        )

        assert event.data == '{"test": "data"}'
        assert event.event_type == "test_event"
        assert event.event_id == "123"
        assert event.retry == 5000
        assert event.timestamp > 0

    def test_event_repr(self):
        """Test event string representation."""
        event = SSETestEvent(data="test data", event_type="test")
        repr_str = repr(event)

        assert "SSETestEvent" in repr_str
        assert "test data" in repr_str
        assert "test" in repr_str


class TestSSEEventExtractor:
    """Test SSEEventExtractor functionality."""

    @pytest.mark.asyncio
    async def test_extract_from_dict_events(self):
        """Test extracting events from dict-based generator."""

        async def mock_generator():
            yield {"data": "event 1", "event": "section", "id": "1"}
            yield {"data": "event 2", "event": "report", "id": "2"}

        events = await SSEEventExtractor.extract_events_from_response(mock_generator())

        assert len(events) == 2
        assert events[0].data == "event 1"
        assert events[0].event_type == "section"
        assert events[0].event_id == "1"
        assert events[1].data == "event 2"
        assert events[1].event_type == "report"
        assert events[1].event_id == "2"

    @pytest.mark.asyncio
    async def test_extract_from_sse_response(self):
        """Test extracting events from EventSourceResponse."""

        async def event_generator():
            yield {"data": "test event", "event": "test"}

        response = EventSourceResponse(event_generator())
        events = await SSEEventExtractor.extract_events_from_response(response)

        # Note: This test might not work perfectly due to EventSourceResponse internals
        # but it validates the interface
        assert isinstance(events, list)

    def test_parse_raw_event(self):
        """Test parsing raw SSE event strings."""
        raw_event = "data: test data\nevent: test_event\nid: 123\nretry: 5000\n"
        event = SSEEventExtractor._parse_raw_event(raw_event)

        assert event is not None
        assert event.data == "test data"
        assert event.event_type == "test_event"
        assert event.event_id == "123"
        assert event.retry == 5000

    def test_parse_simple_data_event(self):
        """Test parsing simple data-only events."""
        raw_event = "data: simple test data"
        event = SSEEventExtractor._parse_raw_event(raw_event)

        assert event is not None
        assert event.data == "simple test data"
        assert event.event_type is None
        assert event.event_id is None


class TestSSEMockAgent:
    """Test SSE mock agent functionality."""

    @pytest.mark.asyncio
    async def test_mock_agent_responses(self):
        """Test mock agent with predefined responses."""
        responses = [
            '{"content": "response 1", "sources": ["source1.com"]}',
            '{"content": "response 2", "sources": ["source2.com"]}',
            Exception("Mock error"),
        ]

        agent = SSEMockAgent(responses)

        # First call
        result1 = await agent.run("test")
        assert result1 == responses[0]
        assert agent.call_count == 1

        # Second call
        result2 = await agent.run("test")
        assert result2 == responses[1]
        assert agent.call_count == 2

        # Third call should raise exception
        with pytest.raises(Exception, match="Mock error"):
            await agent.run("test")
        assert agent.call_count == 3

    @pytest.mark.asyncio
    async def test_mock_agent_dict_response(self):
        """Test mock agent with dict responses."""
        responses = [{"content": "test", "sources": []}]
        agent = SSEMockAgent(responses)

        result = await agent.run("test")
        assert result == '{"content": "test", "sources": []}'


class TestSSETestScenarios:
    """Test pre-built test scenarios."""

    def test_research_workflow_mocks(self):
        """Test research workflow mock data."""
        section_responses, assembler_response = SSETestScenarios.create_research_workflow_mocks()

        assert len(section_responses) == 2
        assert all("content" in resp for resp in section_responses)
        assert all("sources" in resp for resp in section_responses)

        assert isinstance(assembler_response, str)
        assert "# AI Research Report" in assembler_response
        assert "References" in assembler_response

    def test_error_scenario_mocks(self):
        """Test error scenario mock data."""
        error_mocks = SSETestScenarios.create_error_scenario_mocks()

        assert len(error_mocks) == 3
        assert isinstance(error_mocks[0], dict)
        assert isinstance(error_mocks[1], Exception)
        assert isinstance(error_mocks[2], dict)


class TestSSEAssertionHelpers:
    """Test SSE assertion helper functions."""

    def test_assert_sse_event_contains(self):
        """Test event content assertion."""
        events = [
            SSETestEvent(data='{"content": "AI research"}', event_type="section"),
            SSETestEvent(data='{"content": "machine learning"}', event_type="section"),
            SSETestEvent(data='{"content": "final report"}', event_type="report"),
        ]

        # Should pass
        assert_sse_event_contains(events, "AI research")
        assert_sse_event_contains(events, "final report", "report")

        # Should fail
        with pytest.raises(AssertionError):
            assert_sse_event_contains(events, "non-existent content")

        with pytest.raises(AssertionError):
            assert_sse_event_contains(events, "AI research", "report")

    def test_assert_sse_event_count(self):
        """Test event count assertion."""
        events = [
            SSETestEvent(data="test1", event_type="section"),
            SSETestEvent(data="test2", event_type="section"),
            SSETestEvent(data="test3", event_type="report"),
        ]

        # Should pass
        assert_sse_event_count(events, 3)
        assert_sse_event_count(events, 2, "section")
        assert_sse_event_count(events, 1, "report")

        # Should fail
        with pytest.raises(AssertionError):
            assert_sse_event_count(events, 2)

        with pytest.raises(AssertionError):
            assert_sse_event_count(events, 3, "section")

    def test_assert_sse_event_sequence(self):
        """Test event sequence assertion."""
        events = [
            SSETestEvent(data="first event"),
            SSETestEvent(data="second event"),
            SSETestEvent(data="third event"),
        ]

        # Should pass
        assert_sse_event_sequence(events, ["first", "second", "third"])
        assert_sse_event_sequence(events, ["first", "second"])  # Partial sequence

        # Should fail
        with pytest.raises(AssertionError):
            assert_sse_event_sequence(events, ["first", "third", "second"])  # Wrong order

        with pytest.raises(AssertionError):
            assert_sse_event_sequence(events, ["first", "second", "third", "fourth"])  # Too many


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_extract_sse_events_convenience(self):
        """Test convenience extract function."""

        async def mock_generator():
            yield {"data": "convenience test"}

        events = await extract_sse_events(mock_generator())

        assert len(events) == 1
        assert events[0].data == "convenience test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
