"""Tests for agent implementations."""

import pytest
import sys
import os

# Add the backend src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agents import SectionResearcher, ReportAssembler


class TestSectionResearcher:
    """Test cases for SectionResearcher agent."""

    def test_initialization(self):
        """Test that SectionResearcher initializes correctly."""
        section = "Introduction"
        guidelines = "Academic tone, comprehensive coverage"

        researcher = SectionResearcher(section, guidelines)

        # Test basic initialization
        assert researcher.agent is not None
        assert researcher.section == section
        assert researcher.guidelines == guidelines
        assert researcher.instructions is not None  # Instructions should be stored
        assert isinstance(researcher.max_sources, int)
        assert isinstance(researcher.max_content_words, int)

        # Test configuration method
        config = researcher.get_research_config()
        assert config["section"] == section
        assert config["guidelines"] == guidelines

    def test_instructions_contain_section(self):
        """Test that agent instructions contain the section name."""
        section = "Methodology"
        guidelines = "Technical details required"

        researcher = SectionResearcher(section, guidelines)

        # Instructions are stored in the researcher object, not the agent
        assert section in researcher.instructions
        assert guidelines in researcher.instructions

    def test_different_sections(self):
        """Test that different sections create different agents."""
        researcher1 = SectionResearcher("Introduction", "Brief overview")
        researcher2 = SectionResearcher("Conclusion", "Summarize findings")

        # Test that sections are different
        assert researcher1.section != researcher2.section
        assert "Introduction" in researcher1.instructions
        assert "Conclusion" in researcher2.instructions

    def test_agent_tools_configuration(self):
        """Test that agents are properly configured."""
        researcher = SectionResearcher("Methods", "Detailed methodology")

        # Test that the agent exists and instructions are stored
        assert researcher.agent is not None
        assert "Methods" in researcher.instructions
        assert "Detailed methodology" in researcher.instructions

    def test_edge_cases(self):
        """Test edge cases for SectionResearcher."""
        # Empty section name should raise ValueError
        with pytest.raises(ValueError, match="Section title cannot be empty"):
            SectionResearcher("", "Some guidelines")

        # Empty guidelines should work
        researcher2 = SectionResearcher("Section", "")
        assert researcher2.agent is not None
        assert researcher2.guidelines == ""

        # Special characters in section
        researcher3 = SectionResearcher("Section & Analysis", "Guidelines with symbols!")
        assert researcher3.agent is not None
        assert "Section & Analysis" in researcher3.instructions

    @pytest.mark.asyncio
    async def test_agent_mock_run(self):
        """Test agent execution with mocked response."""
        from unittest.mock import AsyncMock, patch

        # Test the new run_research method
        researcher = SectionResearcher("Test Section", "Test guidelines")

        # Mock the agent's run method
        mock_result = '{"content": "Test content", "sources": ["test.com"]}'
        researcher.agent.run = AsyncMock(return_value=mock_result)

        # Test the run_research method
        result = await researcher.run_research("Test query")

        # Verify the result
        assert result["content"] == "Test content"
        assert result["sources"] == ["test.com"]

        # Verify the agent's run method was called with instructions
        researcher.agent.run.assert_called_once()
        call_args = researcher.agent.run.call_args[1]["prompt"]
        assert "Test Section" in call_args
        assert "Test query" in call_args


class TestReportAssembler:
    """Test cases for ReportAssembler agent."""

    def test_initialization(self):
        """Test that ReportAssembler initializes correctly."""
        assembler = ReportAssembler()

        assert assembler.agent is not None
        assert assembler.instructions is not None  # Instructions should be stored
        assert isinstance(assembler.include_metadata, bool)
        assert isinstance(assembler.max_report_length, int)

        # Test configuration method
        config = assembler.get_assembly_config()
        assert "include_metadata" in config
        assert "max_report_length" in config

    def test_instructions_contain_requirements(self):
        """Test that assembler instructions contain formatting requirements."""
        assembler = ReportAssembler()

        instructions = assembler.instructions.lower()
        assert "table of contents" in instructions
        assert "markdown" in instructions
        assert "citations" in instructions or "references" in instructions
        assert "report" in instructions

    def test_assembler_uniqueness(self):
        """Test that multiple assemblers are independent."""
        assembler1 = ReportAssembler()
        assembler2 = ReportAssembler()

        # Should be separate instances
        assert assembler1.agent is not assembler2.agent
        assert assembler1.instructions == assembler2.instructions  # Same instructions is OK

    @pytest.mark.asyncio
    async def test_assembler_mock_run(self):
        """Test assembler execution with mocked response."""
        from unittest.mock import AsyncMock

        # Test the new run_assembly method
        assembler = ReportAssembler()

        # Mock the agent's run method
        mock_result = "# Research Report\n\n## Table of Contents\n\n1. Introduction\n2. Conclusion\n\n## References\n\n[1] Source 1"
        assembler.agent.run = AsyncMock(return_value=mock_result)

        # Test the run_assembly method
        test_sections = (
            '[{"title": "Introduction", "content": "Test content", "sources": ["test.com"]}]'
        )
        result = await assembler.run_assembly(test_sections)

        # Verify the result
        assert "Research Report" in result
        assert "Table of Contents" in result
        assert "References" in result

        # Verify the agent's run method was called with instructions
        assembler.agent.run.assert_called_once()
        call_args = assembler.agent.run.call_args[1]["prompt"]
        assert "markdown" in call_args.lower()
        assert test_sections in call_args

    def test_assembler_instructions_structure(self):
        """Test that assembler instructions are well-structured."""
        assembler = ReportAssembler()
        instructions = assembler.instructions

        # Should contain key formatting requirements
        assert "professional" in instructions.lower() or "polished" in instructions.lower()
        assert len(instructions) > 100  # Should be detailed

        # Should mention key deliverables
        required_terms = ["table of contents", "citations", "references", "markdown"]
        for term in required_terms:
            assert term in instructions.lower(), f"Missing required term: {term}"


class TestAgentIntegration:
    """Integration tests for agent interactions."""

    def test_agent_creation_flow(self):
        """Test that multiple agents can be created for a typical workflow."""
        sections = ["Introduction", "Methodology", "Results", "Conclusion"]
        guidelines = "Academic paper format"

        # Create section researchers
        researchers = []
        for section in sections:
            researcher = SectionResearcher(section, guidelines)
            researchers.append(researcher)
            assert researcher.section == section
            assert section in researcher.instructions

        # Create assembler
        assembler = ReportAssembler()
        assert assembler.agent is not None

        # Verify all agents are unique instances
        agents = [r.agent for r in researchers] + [assembler.agent]
        agent_ids = [id(agent) for agent in agents]
        assert len(set(agent_ids)) == len(agent_ids)  # All unique instances

    def test_concurrent_agent_creation(self):
        """Test that agents can be created concurrently without conflicts."""
        import threading
        import time

        results = []
        errors = []

        def create_agent(section_id):
            try:
                researcher = SectionResearcher(f"Section{section_id}", "Test guidelines")
                results.append(researcher.agent.name)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_agent, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify no errors and all agents created
        assert len(errors) == 0, f"Errors during concurrent creation: {errors}"
        assert len(results) == 5
        assert len(set(results)) == 5  # All unique names

    @pytest.mark.asyncio
    async def test_workflow_simulation(self):
        """Test a complete workflow simulation with mocked agents."""
        from unittest.mock import AsyncMock, patch

        with (
            patch("agents.section_researcher.ReActAgent") as mock_section_agent,
            patch("agents.report_assembler.ReActAgent") as mock_assembler_agent,
        ):

            # Mock section agent
            section_mock = AsyncMock()
            section_mock.run.return_value = (
                '{"content": "Section content", "sources": ["source1.com"]}'
            )
            mock_section_agent.return_value = section_mock

            # Mock assembler agent
            assembler_mock = AsyncMock()
            assembler_mock.run.return_value = "# Complete Report\n\nAssembled content"
            mock_assembler_agent.return_value = assembler_mock

            # Simulate workflow
            sections = ["Introduction", "Conclusion"]
            section_results = []

            # Create and "run" section researchers
            for section in sections:
                researcher = SectionResearcher(section, "Test guidelines")
                # In real workflow, would call researcher.agent.run()
                section_results.append({"section": section, "content": "Test content"})

            # Create and "run" assembler
            assembler = ReportAssembler()
            # In real workflow, would call assembler.agent.run()

            # Verify mocks were called correctly
            assert mock_section_agent.call_count == 2
            assert mock_assembler_agent.call_count == 1
            assert len(section_results) == 2

    def test_memory_efficiency(self):
        """Test memory efficiency when creating many agents."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create many agents
        agents = []
        for i in range(10):
            researcher = SectionResearcher(f"Section{i}", f"Guidelines{i}")
            agents.append(researcher)

        assembler = ReportAssembler()
        agents.append(assembler)

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 200MB for 11 agents)
        max_memory_mb = 200
        memory_increase_mb = memory_increase / 1024 / 1024
        assert (
            memory_increase_mb < max_memory_mb
        ), f"Memory usage too high: {memory_increase_mb:.2f} MB (max: {max_memory_mb} MB)"

        # Cleanup test
        del agents  # All unique names


if __name__ == "__main__":
    pytest.main([__file__])
