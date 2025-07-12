"""
SSE Testing Utilities for Smart Research Crew

This module provides comprehensive utilities for testing Server-Sent Events (SSE)
endpoints and streams in the Smart Research Crew application.
"""

import asyncio
import json
import time
from typing import List, Dict, Any, AsyncIterator, Optional, Union
from unittest.mock import AsyncMock, patch
import pytest
from sse_starlette.sse import EventSourceResponse
from fastapi.testclient import TestClient
from fastapi import Request
import httpx


class SSETestEvent:
    """Represents a parsed SSE event for testing."""

    def __init__(
        self,
        data: str,
        event_type: Optional[str] = None,
        event_id: Optional[str] = None,
        retry: Optional[int] = None,
    ):
        self.data = data
        self.event_type = event_type
        self.event_id = event_id
        self.retry = retry
        self.timestamp = time.time()

    def __repr__(self):
        return f"SSETestEvent(data='{self.data}', type='{self.event_type}', id='{self.event_id}')"


class SSEEventExtractor:
    """Extracts and parses events from SSE responses for testing."""

    @staticmethod
    async def extract_events_from_response(sse_response_coro) -> List[SSETestEvent]:
        """
        Extract events from an SSE response coroutine.

        Args:
            sse_response_coro: Coroutine that returns EventSourceResponse or async generator

        Returns:
            List of SSETestEvent objects
        """
        events = []

        try:
            # Check if sse_response_coro is already an async generator or coroutine
            if hasattr(sse_response_coro, "__aiter__"):
                # It's an async generator, iterate directly
                async for event_data in sse_response_coro:
                    if isinstance(event_data, dict):
                        event = SSETestEvent(
                            data=event_data.get("data", ""),
                            event_type=event_data.get("event"),
                            event_id=event_data.get("id"),
                            retry=event_data.get("retry"),
                        )
                        events.append(event)
                    else:
                        event = SSEEventExtractor._parse_raw_event(str(event_data))
                        if event:
                            events.append(event)
            else:
                # It's a coroutine, await it first
                response = await sse_response_coro

                if isinstance(response, EventSourceResponse):
                    async for chunk in response.body_iterator:
                        event = SSEEventExtractor._parse_chunk(chunk)
                        if event:
                            events.append(event)
                elif hasattr(response, "__aiter__"):
                    # Response is an async generator
                    async for event_data in response:
                        if isinstance(event_data, dict):
                            event = SSETestEvent(
                                data=event_data.get("data", ""),
                                event_type=event_data.get("event"),
                                event_id=event_data.get("id"),
                                retry=event_data.get("retry"),
                            )
                            events.append(event)
                        else:
                            event = SSEEventExtractor._parse_raw_event(str(event_data))
                            if event:
                                events.append(event)
                else:
                    # Single response object
                    if isinstance(response, dict):
                        event = SSETestEvent(
                            data=response.get("data", ""),
                            event_type=response.get("event"),
                            event_id=response.get("id"),
                            retry=response.get("retry"),
                        )
                        events.append(event)
        except Exception as e:
            # Log the error but continue - some tests expect failures
            print(f"SSE extraction error: {e}")

        return events

    @staticmethod
    def _parse_chunk(chunk) -> Optional[SSETestEvent]:
        """Parse a chunk from EventSourceResponse."""
        if isinstance(chunk, dict) and "data" in chunk:
            return SSETestEvent(
                data=chunk["data"],
                event_type=chunk.get("event"),
                event_id=chunk.get("id"),
                retry=chunk.get("retry"),
            )
        elif isinstance(chunk, str) and chunk.startswith("data: "):
            return SSEEventExtractor._parse_raw_event(chunk)
        return None

    @staticmethod
    def _parse_raw_event(event_str: str) -> Optional[SSETestEvent]:
        """Parse a raw SSE event string."""
        lines = event_str.strip().split("\n")
        data = None
        event_type = None
        event_id = None
        retry = None

        for line in lines:
            if line.startswith("data: "):
                data = line[6:]  # Remove 'data: ' prefix
            elif line.startswith("event: "):
                event_type = line[7:]  # Remove 'event: ' prefix
            elif line.startswith("id: "):
                event_id = line[4:]  # Remove 'id: ' prefix
            elif line.startswith("retry: "):
                try:
                    retry = int(line[7:])  # Remove 'retry: ' prefix
                except ValueError:
                    pass

        if data is not None:
            return SSETestEvent(data=data, event_type=event_type, event_id=event_id, retry=retry)
        return None


class SSETestClient:
    """Test client for SSE endpoints with advanced testing capabilities."""

    def __init__(self, app, timeout: float = 30.0):
        self.client = TestClient(app)
        self.timeout = timeout

    async def connect_sse(
        self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None
    ) -> "SSEConnection":
        """
        Connect to an SSE endpoint and return a connection object.

        Args:
            url: SSE endpoint URL
            params: Query parameters
            headers: HTTP headers

        Returns:
            SSEConnection object for managing the connection
        """
        return SSEConnection(self.client, url, params, headers, self.timeout)


class SSEConnection:
    """Manages an SSE connection for testing."""

    def __init__(
        self,
        client: TestClient,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: float = 30.0,
    ):
        self.client = client
        self.url = url
        self.params = params or {}
        self.headers = headers or {}
        self.timeout = timeout
        self.events: List[SSETestEvent] = []
        self.connection_start = None
        self.is_connected = False

    async def start_listening(
        self, max_events: Optional[int] = None, max_duration: Optional[float] = None
    ) -> List[SSETestEvent]:
        """
        Start listening for SSE events.

        Args:
            max_events: Maximum number of events to collect
            max_duration: Maximum duration to listen (seconds)

        Returns:
            List of collected events
        """
        self.connection_start = time.time()
        self.is_connected = True

        try:
            with self.client.stream(
                "GET", self.url, params=self.params, headers=self.headers
            ) as response:
                if response.status_code != 200:
                    raise Exception(f"SSE connection failed: {response.status_code}")

                event_count = 0
                async for line in response.aiter_lines():
                    if not self.is_connected:
                        break

                    if line.startswith("data: "):
                        event = SSEEventExtractor._parse_raw_event(line)
                        if event:
                            self.events.append(event)
                            event_count += 1

                    # Check limits
                    if max_events and event_count >= max_events:
                        break
                    if max_duration and (time.time() - self.connection_start) >= max_duration:
                        break

        except Exception as e:
            print(f"SSE listening error: {e}")
        finally:
            self.is_connected = False

        return self.events

    def disconnect(self):
        """Disconnect from the SSE stream."""
        self.is_connected = False

    def get_events_by_type(self, event_type: str) -> List[SSETestEvent]:
        """Get all events of a specific type."""
        return [event for event in self.events if event.event_type == event_type]

    def get_events_with_data_containing(self, text: str) -> List[SSETestEvent]:
        """Get all events whose data contains the specified text."""
        return [event for event in self.events if text in event.data]


class SSEMockAgent:
    """Mock agent for testing SSE workflows."""

    def __init__(self, responses: List[Union[str, Dict, Exception]]):
        self.responses = responses
        self.call_count = 0

    async def run(self, *args, **kwargs):
        """Mock agent run method."""
        if self.call_count >= len(self.responses):
            raise Exception("No more mock responses available")

        response = self.responses[self.call_count]
        self.call_count += 1

        if isinstance(response, Exception):
            raise response
        elif isinstance(response, dict):
            return json.dumps(response)
        else:
            return response


class SSETestScenarios:
    """Pre-built test scenarios for common SSE testing patterns."""

    @staticmethod
    def create_research_workflow_mocks():
        """Create mocks for a typical research workflow."""
        section_responses = [
            {
                "content": "Introduction content about AI research",
                "sources": ["ai-intro.com", "ai-basics.org"],
            },
            {
                "content": "Methods for conducting AI research",
                "sources": ["methods.edu", "research-guide.net"],
            },
        ]

        assembler_response = """# AI Research Report

## Table of Contents
1. Introduction
2. Methods

## 1. Introduction
Introduction content about AI research

## 2. Methods
Methods for conducting AI research

## References
- [1] ai-intro.com
- [2] ai-basics.org
- [3] methods.edu
- [4] research-guide.net
"""

        return section_responses, assembler_response

    @staticmethod
    def create_error_scenario_mocks():
        """Create mocks for error handling scenarios."""
        return [
            {"content": "Successful section", "sources": ["success.com"]},
            Exception("Network error"),
            {"content": "Recovery section", "sources": ["recovery.com"]},
        ]


class SSEPerformanceTester:
    """Performance testing utilities for SSE endpoints."""

    @staticmethod
    async def measure_throughput(sse_endpoint_func, duration: float = 10.0) -> Dict[str, float]:
        """
        Measure SSE endpoint throughput.

        Args:
            sse_endpoint_func: Function that returns SSE response
            duration: Test duration in seconds

        Returns:
            Performance metrics dictionary
        """
        start_time = time.time()
        event_count = 0
        total_data_size = 0

        try:
            events = await SSEEventExtractor.extract_events_from_response(sse_endpoint_func())

            for event in events:
                if time.time() - start_time >= duration:
                    break
                event_count += 1
                total_data_size += len(event.data.encode("utf-8"))

        except Exception as e:
            print(f"Performance test error: {e}")

        actual_duration = time.time() - start_time

        return {
            "duration": actual_duration,
            "events_per_second": event_count / actual_duration if actual_duration > 0 else 0,
            "total_events": event_count,
            "bytes_per_second": total_data_size / actual_duration if actual_duration > 0 else 0,
            "total_bytes": total_data_size,
        }

    @staticmethod
    async def test_concurrent_connections(sse_endpoint_func, num_connections: int = 5) -> Dict:
        """
        Test concurrent SSE connections.

        Args:
            sse_endpoint_func: Function that returns SSE response
            num_connections: Number of concurrent connections

        Returns:
            Results from concurrent connections
        """

        async def single_connection(connection_id):
            try:
                events = await SSEEventExtractor.extract_events_from_response(sse_endpoint_func())
                return {
                    "connection_id": connection_id,
                    "success": True,
                    "event_count": len(events),
                    "events": events,
                }
            except Exception as e:
                return {
                    "connection_id": connection_id,
                    "success": False,
                    "error": str(e),
                    "event_count": 0,
                }

        tasks = [single_connection(i) for i in range(num_connections)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful_connections = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        total_events = sum(r.get("event_count", 0) for r in results if isinstance(r, dict))

        return {
            "total_connections": num_connections,
            "successful_connections": successful_connections,
            "total_events_across_all_connections": total_events,
            "results": results,
        }


# Pytest fixtures for easy testing
@pytest.fixture
def sse_event_extractor():
    """Provides SSEEventExtractor instance."""
    return SSEEventExtractor()


@pytest.fixture
def reset_sse_app_status():
    """Reset SSE app status for clean test environment."""
    from sse_starlette.sse import AppStatus

    AppStatus.should_exit_event = None
    yield
    AppStatus.should_exit_event = None


@pytest.fixture
def research_workflow_mocks():
    """Provides mocks for research workflow testing."""
    return SSETestScenarios.create_research_workflow_mocks()


@pytest.fixture
def error_scenario_mocks():
    """Provides mocks for error scenario testing."""
    return SSETestScenarios.create_error_scenario_mocks()


# Convenience functions for common testing patterns
async def extract_sse_events(sse_response_coro) -> List[SSETestEvent]:
    """
    Convenience function to extract events from SSE response.
    Maintains backward compatibility with existing test code.
    """
    return await SSEEventExtractor.extract_events_from_response(sse_response_coro)


def assert_sse_event_contains(
    events: List[SSETestEvent], expected_data: str, event_type: str = None
):
    """Assert that events contain data matching the criteria."""
    matching_events = [e for e in events if expected_data in e.data]
    if event_type:
        matching_events = [e for e in matching_events if e.event_type == event_type]

    assert len(matching_events) > 0, f"No events found containing '{expected_data}'" + (
        f" with type '{event_type}'" if event_type else ""
    )


def assert_sse_event_count(events: List[SSETestEvent], expected_count: int, event_type: str = None):
    """Assert the number of events matches expected count."""
    if event_type:
        filtered_events = [e for e in events if e.event_type == event_type]
        assert (
            len(filtered_events) == expected_count
        ), f"Expected {expected_count} events of type '{event_type}', got {len(filtered_events)}"
    else:
        assert len(events) == expected_count, f"Expected {expected_count} events, got {len(events)}"


def assert_sse_event_sequence(events: List[SSETestEvent], expected_sequence: List[str]):
    """Assert events occur in the expected sequence."""
    event_data = [e.data for e in events]
    for i, expected in enumerate(expected_sequence):
        assert i < len(event_data), f"Missing event {i}: '{expected}'"
        assert expected in event_data[i], f"Event {i} doesn't contain '{expected}': {event_data[i]}"
