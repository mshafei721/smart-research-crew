import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.research_service import ResearchService
from src.models import ResearchRequest

@pytest.mark.asyncio
async def test_conduct_research_success():
    with patch("src.services.research_service.SectionResearcher") as MockSectionResearcher:
        with patch("src.services.research_service.ReportAssembler") as MockReportAssembler:

            # Configure mock SectionResearcher instances
            mock_researcher_instance1 = AsyncMock()
            mock_researcher_instance1.run_research.return_value = {"content": "Intro content", "sources": ["intro.com"]}
            mock_researcher_instance2 = AsyncMock()
            mock_researcher_instance2.run_research.return_value = {"content": "Body content", "sources": ["body.com"]}
            MockSectionResearcher.side_effect = [mock_researcher_instance1, mock_researcher_instance2]

            # Configure mock ReportAssembler instance
            mock_assembler_instance = AsyncMock()
            mock_assembler_instance.run_assembly.return_value = "# Final Report"
            MockReportAssembler.return_value = mock_assembler_instance

            service = ResearchService()
            request = ResearchRequest(
                topic="Test Topic",
                guidelines="Test Guidelines",
                sections="Introduction,Body"
            )
            
            events = [event async for event in service.conduct_research(request)]

            assert len(events) > 0
            assert events[0]["event"] == "start"
            assert any(e["event"] == "section_complete" for e in events)
            assert any(e["event"] == "report_complete" for e in events)
            assert events[-1]["event"] == "end"
            

@pytest.mark.asyncio
async def test_conduct_research_section_failure():
    with patch("src.services.research_service.SectionResearcher") as MockSectionResearcher:
        with patch("src.services.research_service.ReportAssembler") as MockReportAssembler:

            # Configure mock SectionResearcher instances, one failing
            mock_researcher_instance1 = AsyncMock()
            mock_researcher_instance1.run_research.return_value = {"content": "Intro content", "sources": ["intro.com"]}
            mock_researcher_instance2 = AsyncMock()
            mock_researcher_instance2.run_research.side_effect = Exception("Research failed for body")
            MockSectionResearcher.side_effect = [mock_researcher_instance1, mock_researcher_instance2]

            # Configure mock ReportAssembler instance (should not be called)
            mock_assembler_instance = AsyncMock()
            MockReportAssembler.return_value = mock_assembler_instance

            service = ResearchService()
            request = ResearchRequest(
                topic="Test Topic",
                guidelines="Test Guidelines",
                sections="Introduction,Body"
            )
            
            events = []
            with pytest.raises(RuntimeError, match="Section research failed for 'Body'"):
                async for event in service.conduct_research(request):
                    events.append(event)

            assert len(events) > 0
            assert events[0]["event"] == "start"
            assert any(e["event"] == "section_error" for e in events)

            assert MockSectionResearcher.call_count == 2
            mock_assembler_instance.run_assembly.assert_not_called()

@pytest.mark.asyncio
async def test_conduct_research_assembly_failure():
    with patch("src.services.research_service.SectionResearcher") as MockSectionResearcher:
        with patch("src.services.research_service.ReportAssembler") as MockReportAssembler:

            # Configure mock SectionResearcher instances (all succeed)
            mock_researcher_instance1 = AsyncMock()
            mock_researcher_instance1.run_research.return_value = {"content": "Intro content", "sources": ["intro.com"]}
            mock_researcher_instance2 = AsyncMock()
            mock_researcher_instance2.run_research.return_value = {"content": "Body content", "sources": ["body.com"]}
            MockSectionResearcher.side_effect = [mock_researcher_instance1, mock_researcher_instance2]

            # Configure mock ReportAssembler instance to fail
            mock_assembler_instance = AsyncMock()
            mock_assembler_instance.run_assembly.side_effect = Exception("Assembly failed")
            MockReportAssembler.return_value = mock_assembler_instance

            service = ResearchService()
            request = ResearchRequest(
                topic="Test Topic",
                guidelines="Test Guidelines",
                sections="Introduction,Body"
            )
            
            events = []
            with pytest.raises(RuntimeError, match="Assembly failed"):
                async for event in service.conduct_research(request):
                    events.append(event)

            assert len(events) > 0
            assert events[0]["event"] == "start"
            assert any(e["event"] == "assembly_error" for e in events)
