"""
Testing utilities for Smart Research Crew.

This package provides utilities for testing SSE endpoints, agents, and integration scenarios.
"""

from .sse_test_utils import (
    SSETestEvent,
    SSEEventExtractor,
    SSETestClient,
    SSEConnection,
    SSEMockAgent,
    SSETestScenarios,
    SSEPerformanceTester,
    extract_sse_events,
    assert_sse_event_contains,
    assert_sse_event_count,
    assert_sse_event_sequence,
)

__all__ = [
    "SSETestEvent",
    "SSEEventExtractor",
    "SSETestClient",
    "SSEConnection",
    "SSEMockAgent",
    "SSETestScenarios",
    "SSEPerformanceTester",
    "extract_sse_events",
    "assert_sse_event_contains",
    "assert_sse_event_count",
    "assert_sse_event_sequence",
]
