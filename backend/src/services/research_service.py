import asyncio
import json
from typing import List, Dict, Any

from src.agents.section_researcher import SectionResearcher
from src.agents.report_assembler import ReportAssembler
from src.models import ResearchRequest, ResearchSection
from src.config.logging import LoggerMixin, log_performance

class ResearchService(LoggerMixin):
    """
    Service responsible for orchestrating the research process.

    This service coordinates between SectionResearcher agents and the ReportAssembler
    to fulfill a complete research request.
    """

    async def conduct_research(self, request: ResearchRequest) -> str:
        """
        Conducts a full research process based on the given request.

        Args:
            request: The ResearchRequest object containing topic, guidelines, and sections.

        Returns:
            The final assembled report in Markdown format.

        Raises:
            RuntimeError: If any part of the research process fails.
        """
        self.log_info("Starting research process", topic=request.topic, sections=request.sections)

        sections_to_research = [s.strip() for s in request.sections.split(",")]
        researched_sections: List[Dict[str, Any]] = []

        # Step 1: Research each section concurrently
        async with log_performance("Section Research Phase", self.logger):
            tasks = []
            for section_title in sections_to_research:
                researcher = SectionResearcher(
                    section=section_title,
                    guidelines=request.guidelines,
                )
                tasks.append(researcher.run_research(query=f"{request.topic} {section_title}"))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                section_title = sections_to_research[i]
                if isinstance(result, Exception):
                    self.log_error(
                        f"Failed to research section '{section_title}': {result}",
                        exc_info=True,
                    )
                    # Depending on requirements, you might skip this section or raise an error
                    raise RuntimeError(f"Section research failed for '{section_title}')")
                
                researched_sections.append({
                    "title": section_title,
                    "content": result["content"],
                    "sources": result["sources"],
                })

        # Step 2: Assemble the report
        try:
            async with log_performance("Report Assembly Phase", self.logger):
                assembler = ReportAssembler()
                final_report = await assembler.run_assembly(json.dumps(researched_sections))
        except Exception as e:
            self.log_error("Report assembly failed", exc_info=True)
            raise RuntimeError(f"Assembly failed: {str(e)}") from e

        self.log_info("Research process completed successfully", topic=request.topic)
        return final_report
