"""Integration tests for the Smart Research Crew backend."""

import pytest
import sys
import os
from unittest.mock import AsyncMock, patch

# Add the backend src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agents import SectionResearcher, ReportAssembler  # noqa: E402


class TestBackendIntegration:
    """Integration tests for backend components."""

    def test_import_structure(self):
        """Test that all backend modules can be imported correctly."""
        from agents import SectionResearcher, ReportAssembler
        from api import router
        from utils import ask

        assert SectionResearcher is not None
        assert ReportAssembler is not None
        assert router is not None
        assert ask is not None

    def test_agent_workflow_setup(self):
        """Test that agents can be set up for a typical workflow."""
        sections = ["Introduction", "Methods", "Results"]
        guidelines = "Academic format with citations"

        # Create section researchers
        researchers = [SectionResearcher(section, guidelines) for section in sections]

        # Create assembler
        assembler = ReportAssembler()

        # Verify all components exist
        assert len(researchers) == 3
        assert all(r.agent is not None for r in researchers)
        assert assembler.agent is not None

        # Verify unique agent names
        names = [r.agent.name for r in researchers] + [assembler.agent.name]
        assert len(set(names)) == len(names)  # All unique

    @pytest.mark.asyncio
    @patch("agents.section_researcher.ReActAgent")
    async def test_mocked_research_flow(self, mock_react_agent):
        """Test research flow with mocked agents."""
        # Mock the ReActAgent
        mock_agent_instance = AsyncMock()
        mock_agent_instance.run.return_value = (
            '{"content": "Test research content", "sources": ["example.com"]}'
        )
        mock_react_agent.return_value = mock_agent_instance

        # Test section research
        researcher = SectionResearcher("Introduction", "Academic tone")

        # The agent should be properly initialized
        assert researcher.agent is not None
        mock_react_agent.assert_called_once()

        # Verify the agent was configured correctly
        call_args = mock_react_agent.call_args
        assert call_args[1]["name"] == "SectionAgent-Introduction"
        assert "Introduction" in call_args[1]["instructions"]
        assert "Academic tone" in call_args[1]["instructions"]

    def test_memory_usage(self):
        """Test that memory usage is reasonable for agent creation."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create multiple agents
        researchers = []
        for i in range(5):
            researcher = SectionResearcher(f"Section{i}", "Test guidelines")
            researchers.append(researcher)

        ReportAssembler()

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB)
        assert (
            memory_increase < 100 * 1024 * 1024
        ), f"Memory usage too high: {memory_increase / 1024 / 1024:.2f} MB"


if __name__ == "__main__":
    pytest.main([__file__])
