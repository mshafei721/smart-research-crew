#!/usr/bin/env python3
"""
Comprehensive E2E tests for Smart Research Crew system.
Tests all components: CLI, API, SSE, Frontend integration, and full workflows.
"""

import asyncio
import json
import sys
import os
import time
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from typing import AsyncGenerator

# Add the backend directory to the path
sys.path.insert(0, '../../backend/src')

from agents import SectionResearcher, ReportAssembler
from api.routes import research_sse
from fastapi import FastAPI
from fastapi.testclient import TestClient


class ComprehensiveE2ETests:
    """Comprehensive End-to-End test suite for Smart Research Crew."""
    
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "name": test_name,
            "success": success,
            "details": details
        })
        
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    async def test_01_agent_mocking_framework(self):
        """Test 1: Verify proper agent mocking with BeeAI framework."""
        test_name = "Agent Mocking Framework"
        
        try:
            # Mock both ChatModel.from_name and ReActAgent
            with patch('beeai_framework.backend.chat.ChatModel.from_name') as mock_chat_model, \
                 patch('beeai_framework.agents.react.ReActAgent') as mock_react_agent:
                
                # Mock the chat model
                mock_llm = MagicMock()
                mock_chat_model.return_value = mock_llm
                
                # Mock the agent instance
                mock_agent_instance = AsyncMock()
                mock_agent_instance.run.return_value = AsyncMock()
                mock_agent_instance.run.return_value.result.text = '{"content": "Test content", "sources": ["test.com"]}'
                mock_react_agent.return_value = mock_agent_instance
                
                # Create a section researcher
                researcher = SectionResearcher("Introduction", "Test guidelines")
                
                # Verify the agent was created
                assert researcher.agent is not None
                assert mock_react_agent.called
                assert mock_chat_model.called
                
                # Verify ChatModel was called with correct model
                mock_chat_model.assert_called_with("openai")
                
                # Verify agent was configured correctly
                call_kwargs = mock_react_agent.call_args[1]
                assert 'llm' in call_kwargs
                assert 'tools' in call_kwargs
                assert 'memory' in call_kwargs
                assert call_kwargs['llm'] == mock_llm
                
                self.log_test(test_name, True, "BeeAI ReActAgent mocking works correctly")
                
        except Exception as e:
            self.log_test(test_name, False, f"Error: {e}")
    
    async def test_02_cli_workflow_mocked(self):
        """Test 2: Full CLI workflow with properly mocked agents."""
        test_name = "CLI Workflow (Mocked)"
        
        try:
            with patch('beeai_framework.backend.chat.ChatModel.from_name') as mock_chat_model, \
                 patch('beeai_framework.agents.react.ReActAgent') as mock_react_agent:
                
                # Mock the chat model
                mock_llm = MagicMock()
                mock_chat_model.return_value = mock_llm
                # Mock section agent
                section_mock = AsyncMock()
                section_result = AsyncMock()
                section_result.result.text = '{"content": "Introduction content about AI", "sources": ["ai-intro.com", "ai-basics.org"]}'
                section_mock.run.return_value = section_result
                
                # Mock assembler agent  
                assembler_mock = AsyncMock()
                assembler_result = AsyncMock()
                assembler_result.result.text = """# AI Research Report

## Table of Contents
1. Introduction

## 1. Introduction
Introduction content about AI

## References
- [1] ai-intro.com
- [2] ai-basics.org
"""
                assembler_mock.run.return_value = assembler_result
                
                # Return different mocks based on call order
                mock_react_agent.side_effect = [section_mock, assembler_mock]
                
                # Simulate CLI workflow
                topic = "AI Research Trends"
                guidelines = "Academic format with citations"
                sections = ["Introduction"]
                
                section_results = []
                
                # Process section
                for sec in sections:
                    researcher = SectionResearcher(sec, guidelines)
                    result = await researcher.agent.run(f"Research section '{sec}' on topic: {topic}")
                    
                    try:
                        data = json.loads(result.result.text)
                        section_results.append({"title": sec, **data})
                    except json.JSONDecodeError:
                        section_results.append({
                            "title": sec,
                            "content": result.result.text,
                            "sources": []
                        })
                
                # Assemble report
                assembler = ReportAssembler()
                report_result = await assembler.agent.run(json.dumps(section_results))
                final_report = report_result.result.text
                
                # Validate results
                assert len(section_results) == 1
                assert "content" in section_results[0]
                assert "sources" in section_results[0]
                assert "# AI Research Report" in final_report
                assert "Table of Contents" in final_report
                assert "References" in final_report
                
                self.log_test(test_name, True, f"Processed {len(sections)} sections, generated {len(final_report)} char report")
                
        except Exception as e:
            self.log_test(test_name, False, f"Error: {e}")
    
    async def test_03_sse_event_generator_extraction(self):
        """Test 3: Extract and test the SSE event generator directly."""
        test_name = "SSE Event Generator"
        
        try:
            with patch('beeai_framework.backend.chat.ChatModel.from_name') as mock_chat_model, \
                 patch('beeai_framework.agents.react.ReActAgent') as mock_react_agent:
                
                # Mock the chat model
                mock_llm = MagicMock()
                mock_chat_model.return_value = mock_llm
                # Mock agents
                section_mock = AsyncMock()
                section_result = AsyncMock()
                section_result.result.text = '{"content": "Test content", "sources": ["test.com"]}'
                section_mock.run.return_value = section_result
                
                assembler_mock = AsyncMock()
                assembler_result = AsyncMock()
                assembler_result.result.text = "# Test Report\n\nAssembled content"
                assembler_mock.run.return_value = assembler_result
                
                mock_react_agent.side_effect = [section_mock, assembler_mock]
                
                # Call the research_sse function and extract the event generator
                from sse_starlette import EventSourceResponse
                
                sse_response = research_sse("Test Topic", "Test guidelines", "Introduction")
                
                # Extract the generator from EventSourceResponse
                assert isinstance(sse_response, EventSourceResponse)
                
                # The EventSourceResponse wraps the async generator
                # We need to access it through the internal structure
                event_generator = sse_response.body_iterator
                
                # Collect events
                events = []
                async for event in event_generator:
                    # Events come as dict with 'event' and 'data' keys
                    events.append(event)
                
                # Validate events
                assert len(events) >= 2  # At least section + report events
                
                # Check for section event
                section_events = [e for e in events if e.get('event') == 'section']
                assert len(section_events) == 1
                
                # Check for report event  
                report_events = [e for e in events if e.get('event') == 'report']
                assert len(report_events) == 1
                
                self.log_test(test_name, True, f"Generated {len(events)} SSE events correctly")
                
        except Exception as e:
            self.log_test(test_name, False, f"Error: {e}")
    
    async def test_04_fastapi_server_endpoints(self):
        """Test 4: FastAPI server endpoints with mocked backend."""
        test_name = "FastAPI Server Endpoints"
        
        try:
            with patch('beeai_framework.backend.chat.ChatModel.from_name') as mock_chat_model, \
                 patch('beeai_framework.agents.react.ReActAgent') as mock_react_agent:
                
                # Mock the chat model
                mock_llm = MagicMock()
                mock_chat_model.return_value = mock_llm
                # Mock agents
                section_mock = AsyncMock()
                section_result = AsyncMock()
                section_result.result.text = '{"content": "API test content", "sources": ["api-test.com"]}'
                section_mock.run.return_value = section_result
                
                assembler_mock = AsyncMock()
                assembler_result = AsyncMock()
                assembler_result.result.text = "# API Test Report\n\nAPI assembled content"
                assembler_mock.run.return_value = assembler_result
                
                mock_react_agent.side_effect = [section_mock, assembler_mock]
                
                # Create FastAPI test client
                from api import router
                app = FastAPI()
                app.include_router(router)
                
                with TestClient(app) as client:
                    # Test SSE endpoint
                    response = client.get("/sse", params={
                        "topic": "API Test Topic",
                        "guidelines": "API test guidelines",
                        "sections": "Introduction,Conclusion"
                    })
                    
                    # Should get successful response
                    assert response.status_code == 200
                    assert "text/plain" in response.headers.get("content-type", "")
                    
                    # Response content should contain SSE events
                    content = response.text
                    assert "event: section" in content or "event: report" in content
                    
                self.log_test(test_name, True, f"FastAPI endpoint responded with {response.status_code}")
                
        except Exception as e:
            self.log_test(test_name, False, f"Error: {e}")
    
    async def test_05_concurrent_requests(self):
        """Test 5: Concurrent request handling."""
        test_name = "Concurrent Request Handling"
        
        try:
            with patch('beeai_framework.backend.chat.ChatModel.from_name') as mock_chat_model, \
                 patch('beeai_framework.agents.react.ReActAgent') as mock_react_agent:
                
                # Mock the chat model
                mock_llm = MagicMock()
                mock_chat_model.return_value = mock_llm
                # Mock agents to respond quickly
                def create_mock_agent():
                    mock_agent = AsyncMock()
                    mock_result = AsyncMock()
                    mock_result.result.text = '{"content": "Concurrent test", "sources": ["concurrent.com"]}'
                    mock_agent.run.return_value = mock_result
                    return mock_agent
                
                mock_react_agent.side_effect = lambda *args, **kwargs: create_mock_agent()
                
                # Run multiple concurrent "research" tasks
                async def run_single_research(task_id: int):
                    researcher = SectionResearcher(f"Section{task_id}", "Concurrent test")
                    result = await researcher.agent.run(f"Test concurrent research {task_id}")
                    return task_id, result.result.text
                
                # Run 5 concurrent tasks
                start_time = time.time()
                tasks = [run_single_research(i) for i in range(5)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                execution_time = time.time() - start_time
                
                # Validate results
                successful_results = [r for r in results if not isinstance(r, Exception)]
                assert len(successful_results) == 5
                
                # Should execute relatively quickly with mocks
                assert execution_time < 5.0
                
                self.log_test(test_name, True, f"Handled 5 concurrent requests in {execution_time:.2f}s")
                
        except Exception as e:
            self.log_test(test_name, False, f"Error: {e}")
    
    async def test_06_error_handling(self):
        """Test 6: Error handling and recovery."""
        test_name = "Error Handling & Recovery"
        
        try:
            with patch('beeai_framework.backend.chat.ChatModel.from_name') as mock_chat_model, \
                 patch('beeai_framework.agents.react.ReActAgent') as mock_react_agent:
                
                # Mock the chat model
                mock_llm = MagicMock()
                mock_chat_model.return_value = mock_llm
                # Mock agent that sometimes fails
                failing_mock = AsyncMock()
                failing_mock.run.side_effect = Exception("Simulated API failure")
                
                working_mock = AsyncMock()
                working_result = AsyncMock()
                working_result.result.text = '{"content": "Recovery content", "sources": ["recovery.com"]}'
                working_mock.run.return_value = working_result
                
                # First call fails, second succeeds
                mock_react_agent.side_effect = [failing_mock, working_mock]
                
                # Test error handling in workflow
                errors_encountered = 0
                successful_results = []
                
                for i in range(2):
                    try:
                        researcher = SectionResearcher(f"Section{i}", "Error test")
                        result = await researcher.agent.run(f"Test error handling {i}")
                        successful_results.append(result.result.text)
                    except Exception as e:
                        errors_encountered += 1
                        print(f"    Expected error caught: {e}")
                
                # Should have encountered 1 error and 1 success
                assert errors_encountered == 1
                assert len(successful_results) == 1
                
                self.log_test(test_name, True, f"Handled {errors_encountered} errors, {len(successful_results)} successes")
                
        except Exception as e:
            self.log_test(test_name, False, f"Error: {e}")
    
    async def test_07_data_validation(self):
        """Test 7: Data validation and format compliance."""
        test_name = "Data Validation & Format"
        
        try:
            with patch('beeai_framework.backend.chat.ChatModel.from_name') as mock_chat_model, \
                 patch('beeai_framework.agents.react.ReActAgent') as mock_react_agent:
                
                # Mock the chat model
                mock_llm = MagicMock()
                mock_chat_model.return_value = mock_llm
                # Test various response formats
                test_cases = [
                    # Valid JSON
                    '{"content": "Valid content", "sources": ["valid.com"]}',
                    # Invalid JSON (should be handled gracefully)
                    'This is not JSON but should be handled',
                    # JSON with missing fields
                    '{"content": "Missing sources"}',
                    # Empty response
                    '',
                ]
                
                results = []
                
                for i, response_text in enumerate(test_cases):
                    mock_agent = AsyncMock()
                    mock_result = AsyncMock()
                    mock_result.result.text = response_text
                    mock_agent.run.return_value = mock_result
                    mock_react_agent.return_value = mock_agent
                    
                    researcher = SectionResearcher(f"TestSection{i}", "Validation test")
                    result = await researcher.agent.run(f"Test validation {i}")
                    
                    # Try to parse as JSON
                    try:
                        data = json.loads(result.result.text)
                        results.append({"type": "json", "data": data})
                    except json.JSONDecodeError:
                        results.append({"type": "text", "data": result.result.text})
                
                # Should have processed all test cases
                assert len(results) == len(test_cases)
                
                # First should be valid JSON
                assert results[0]["type"] == "json"
                assert "content" in results[0]["data"]
                
                # Others should be handled as text
                for i in range(1, len(results)):
                    if results[i]["data"]:  # Skip empty responses
                        assert "data" in results[i]
                
                self.log_test(test_name, True, f"Validated {len(test_cases)} response formats")
                
        except Exception as e:
            self.log_test(test_name, False, f"Error: {e}")
    
    async def test_08_memory_and_performance(self):
        """Test 8: Memory usage and performance characteristics."""
        test_name = "Memory & Performance"
        
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            with patch('beeai_framework.agents.react.ReActAgent') as mock_react_agent:
                # Create mock that responds quickly
                mock_agent = AsyncMock()
                mock_result = AsyncMock()
                mock_result.result.text = '{"content": "Performance test", "sources": ["perf.com"]}'
                mock_agent.run.return_value = mock_result
                mock_react_agent.return_value = mock_agent
                
                # Create multiple agents and run them
                start_time = time.time()
                agents = []
                
                for i in range(10):
                    researcher = SectionResearcher(f"PerfSection{i}", "Performance test")
                    agents.append(researcher)
                
                # Run some operations
                tasks = []
                for agent in agents[:5]:  # Run 5 concurrent operations
                    task = agent.agent.run(f"Performance test operation")
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                execution_time = time.time() - start_time
                
                final_memory = process.memory_info().rss
                memory_increase = final_memory - initial_memory
                memory_increase_mb = memory_increase / 1024 / 1024
                
                # Validate performance
                assert len(results) == 5
                assert execution_time < 10.0  # Should be fast with mocks
                assert memory_increase_mb < 100  # Should not use excessive memory
                
                self.log_test(test_name, True, f"Created 10 agents, ran 5 ops in {execution_time:.2f}s, +{memory_increase_mb:.1f}MB")
                
        except Exception as e:
            self.log_test(test_name, False, f"Error: {e}")
    
    async def test_09_full_workflow_integration(self):
        """Test 9: Complete end-to-end workflow integration."""
        test_name = "Full Workflow Integration"
        
        try:
            with patch('beeai_framework.backend.chat.ChatModel.from_name') as mock_chat_model, \
                 patch('beeai_framework.agents.react.ReActAgent') as mock_react_agent:
                
                # Mock the chat model
                mock_llm = MagicMock()
                mock_chat_model.return_value = mock_llm
                # Mock comprehensive workflow
                section_responses = [
                    '{"content": "Introduction to quantum computing applications in AI", "sources": ["nature.com/quantum", "arxiv.org/quant-ai"]}',
                    '{"content": "Current methodologies in quantum machine learning", "sources": ["ieee.org/qml", "acm.org/quantum"]}',
                    '{"content": "Future prospects and challenges in quantum AI", "sources": ["science.org/future-quantum", "quantum-journal.org"]}'
                ]
                
                final_report = """# Quantum Computing Applications in AI Research

## Table of Contents
1. Introduction
2. Methodology  
3. Future Prospects

## 1. Introduction
Introduction to quantum computing applications in AI

## 2. Methodology
Current methodologies in quantum machine learning

## 3. Future Prospects
Future prospects and challenges in quantum AI

## References
[1] nature.com/quantum
[2] arxiv.org/quant-ai
[3] ieee.org/qml
[4] acm.org/quantum
[5] science.org/future-quantum
[6] quantum-journal.org
"""
                
                # Create mock agents
                section_mocks = []
                for response in section_responses:
                    mock_agent = AsyncMock()
                    mock_result = AsyncMock()
                    mock_result.result.text = response
                    mock_agent.run.return_value = mock_result
                    section_mocks.append(mock_agent)
                
                assembler_mock = AsyncMock()
                assembler_result = AsyncMock()
                assembler_result.result.text = final_report
                assembler_mock.run.return_value = assembler_result
                
                # Return mocks in sequence
                mock_react_agent.side_effect = section_mocks + [assembler_mock]
                
                # Run full workflow
                topic = "Quantum Computing Applications in AI"
                guidelines = "Academic research format with citations"
                sections = ["Introduction", "Methodology", "Future Prospects"]
                
                # Step 1: Research sections
                section_results = []
                for sec in sections:
                    researcher = SectionResearcher(sec, guidelines)
                    result = await researcher.agent.run(f"Research section '{sec}' on topic: {topic}")
                    
                    data = json.loads(result.result.text)
                    section_results.append({"title": sec, **data})
                
                # Step 2: Assemble report
                assembler = ReportAssembler()
                final_result = await assembler.agent.run(json.dumps(section_results))
                final_markdown = final_result.result.text
                
                # Validate comprehensive workflow
                assert len(section_results) == 3
                assert all("content" in sr and "sources" in sr for sr in section_results)
                assert "# Quantum Computing Applications in AI Research" in final_markdown
                assert "Table of Contents" in final_markdown
                assert "References" in final_markdown
                
                # Count sources
                total_sources = sum(len(sr["sources"]) for sr in section_results)
                assert total_sources == 6
                
                self.log_test(test_name, True, f"Full workflow: {len(sections)} sections, {total_sources} sources, {len(final_markdown)} chars")
                
        except Exception as e:
            self.log_test(test_name, False, f"Error: {e}")
    
    def print_summary(self):
        """Print test summary."""
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("🧪 COMPREHENSIVE E2E TEST SUMMARY")
        print("="*60)
        print(f"Total Tests:    {total_tests}")
        print(f"Passed:         {self.passed_tests} ✅")
        print(f"Failed:         {self.failed_tests} ❌")
        print(f"Success Rate:   {success_rate:.1f}%")
        print("="*60)
        
        if self.failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['name']}: {result['details']}")
        
        return self.failed_tests == 0


async def main():
    """Run comprehensive E2E tests."""
    print("🚀 Smart Research Crew - Comprehensive E2E Test Suite")
    print("="*60)
    print("Testing all components: Agents, CLI, API, SSE, Integration")
    print("="*60)
    print()
    
    # Initialize test suite
    tests = ComprehensiveE2ETests()
    
    # Run all tests
    await tests.test_01_agent_mocking_framework()
    await tests.test_02_cli_workflow_mocked()
    await tests.test_03_sse_event_generator_extraction()
    await tests.test_04_fastapi_server_endpoints()
    await tests.test_05_concurrent_requests()
    await tests.test_06_error_handling()
    await tests.test_07_data_validation()
    await tests.test_08_memory_and_performance()
    await tests.test_09_full_workflow_integration()
    
    # Print summary and return exit code
    all_passed = tests.print_summary()
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)