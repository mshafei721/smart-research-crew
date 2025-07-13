"""
Smart Research Crew - Report Assembler Agent

Intelligent agent responsible for assembling individual research sections
into a cohesive, professionally formatted report.
"""

import textwrap
import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend.chat import ChatModel
from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory

from config import get_settings
from config.logging import LoggerMixin, get_logger


class ReportAssembler(LoggerMixin):
    """
    Agent responsible for assembling research sections into a unified report.

    This agent takes structured JSON data from multiple research sections
    and creates a professionally formatted Markdown report with proper
    citations, table of contents, and unified formatting.

    Attributes:
        agent (ReActAgent): The underlying BeeAI agent instance
        settings: Application settings for configuration

    Input Format:
        List of section objects:
        [
            {
                "title": "Section Title",
                "content": "Markdown content with citations",
                "sources": ["url1", "url2", "url3"]
            }
        ]

    Output Format:
        Unified Markdown report with:
        - Document title
        - Table of contents
        - Numbered sections
        - Deduplicated references

    Example:
        >>> assembler = ReportAssembler()
        >>> sections = [{"title": "Intro", "content": "...", "sources": [...]}]
        >>> report = await assembler.agent.run(json.dumps(sections))
    """

    def __init__(self, include_metadata: bool = True, max_report_length: int = 10000):
        """
        Initialize the Report Assembler agent.

        Args:
            include_metadata: Whether to include report metadata (default: True)
            max_report_length: Maximum report length in characters (default: 10000)

        Raises:
            RuntimeError: If agent initialization fails
        """
        self.include_metadata = include_metadata
        self.max_report_length = max_report_length
        self.settings = get_settings()

        self.log_info(
            "Initializing ReportAssembler",
            include_metadata=include_metadata,
            max_report_length=max_report_length,
        )

        # Store instructions for later use in run-time prompts
        self.instructions = self._create_instructions()

        # Initialize the agent with configured model (no instructions parameter)
        try:
            self.agent = ReActAgent(
                llm=ChatModel.from_name(self.settings.llm_model),
                tools=[],  # No tools needed for assembly
                memory=UnconstrainedMemory(),
            )

            self.log_info("ReportAssembler initialized successfully")

        except Exception as e:
            self.log_error("Failed to initialize ReportAssembler", exc_info=True)
            raise RuntimeError(f"Agent initialization failed: {str(e)}") from e

    def _create_instructions(self) -> str:
        """
        Create detailed instructions for the report assembly agent.

        Returns:
            Formatted instruction string for the agent
        """
        metadata_section = ""
        if self.include_metadata:
            metadata_section = """
            ## Report Information
            - **Generated**: {current_date}
            - **Total Sections**: {section_count}
            - **Sources Referenced**: {source_count}
            
            """

        instructions = textwrap.dedent(
            f"""
            You are a specialized report assembly agent responsible for creating unified, 
            professional research reports from structured section data.
            
            INPUT FORMAT:
            You will receive a JSON array of section objects with this structure:
            [{{"title": "Section Title", "content": "markdown content", "sources": ["url1", "url2"]}}]
            
            OUTPUT REQUIREMENTS:
            Create a polished, unified Markdown report following this EXACT structure:
            
            # [Intelligent Report Title Based on Content]
            {metadata_section}
            ## Executive Summary
            [2-3 sentence overview of the key findings and insights]
            
            ## Table of Contents
            1. [Section 1 Name]
            2. [Section 2 Name]
            3. [Additional sections as needed]
            
            ## 1. [Section 1 Name]
            [Section content with proper citations [1], [2], etc.]
            
            ## 2. [Section 2 Name]
            [Section content with proper citations continuing numbering]
            
            [Continue for all sections...]
            
            ## Key Insights
            [3-5 bullet points summarizing the most important findings across all sections]
            
            ## References
            [1] First Source URL
            [2] Second Source URL
            [Deduplicated list of all sources in order of appearance]
            
            PROCESSING REQUIREMENTS:
            1. **Intelligent Title Generation**: Create a descriptive title based on the section content themes
            2. **Executive Summary**: Synthesize key points from all sections into 2-3 sentences
            3. **Content Integration**: Ensure smooth flow between sections
            4. **Citation Management**: Renumber citations sequentially across the entire document
            5. **Source Deduplication**: Remove duplicate sources and maintain proper numbering
            6. **Quality Enhancement**: Fix any formatting inconsistencies or grammatical issues
            7. **Key Insights**: Extract and highlight the most important findings
            
            FORMATTING STANDARDS:
            - Use consistent heading hierarchy (# for title, ## for main sections)
            - Maintain proper Markdown formatting throughout
            - Ensure citations are properly formatted as [1], [2], etc.
            - Include proper line breaks and spacing
            - Maximum report length: {self.max_report_length} characters
            
            CONTENT QUALITY:
            - Preserve all original research content and findings
            - Maintain academic tone and professional presentation
            - Ensure logical flow and coherent narrative
            - Include all relevant sources and citations
            - Add transitional text between sections if needed for coherence
            
            OUTPUT CONSTRAINTS:
            - Return ONLY the final Markdown content
            - No explanations, comments, or additional text
            - Ensure proper Markdown syntax throughout
            - Must be complete and ready for immediate use
            
            EXAMPLE STRUCTURE:
            # Artificial Intelligence in Healthcare: Current Trends and Future Prospects
            
            ## Report Information
            - **Generated**: January 15, 2024
            - **Total Sections**: 3
            - **Sources Referenced**: 8
            
            ## Executive Summary
            This report examines the current state of AI in healthcare, highlighting significant advances in diagnostic imaging and treatment personalization. The analysis reveals both promising opportunities and important challenges that must be addressed for successful implementation.
            
            ## Table of Contents
            1. Current AI Applications in Diagnostics
            2. Treatment Personalization Technologies
            3. Implementation Challenges and Solutions
            
            ## 1. Current AI Applications in Diagnostics
            [Content with citations]
            
            ## 2. Treatment Personalization Technologies
            [Content with citations]
            
            ## 3. Implementation Challenges and Solutions
            [Content with citations]
            
            ## Key Insights
            - AI diagnostic tools show 95% accuracy in medical imaging applications [1]
            - Personalized treatment protocols reduce adverse reactions by 40% [3]
            - Implementation costs remain the primary barrier for smaller healthcare facilities [5]
            
            ## References
            [1] https://medical-journal.edu/ai-diagnostics-2024
            [2] https://healthcare-tech.org/personalization-study
            [Continuing with all sources...]
        """
        )

        return instructions

    def validate_input(self, input_data: str) -> List[Dict[str, Any]]:
        """
        Validate input section data format and content.

        Args:
            input_data: JSON string containing section data

        Returns:
            Parsed and validated section data

        Raises:
            ValueError: If input format is invalid
        """
        try:
            sections = json.loads(input_data)

            if not isinstance(sections, list):
                raise ValueError("Input must be a JSON array of section objects")

            if not sections:
                raise ValueError("At least one section is required")

            if len(sections) > self.settings.max_sections:
                raise ValueError(
                    f"Too many sections: {len(sections)} > {self.settings.max_sections}"
                )

            validated_sections = []
            all_sources = set()

            for i, section in enumerate(sections):
                if not isinstance(section, dict):
                    raise ValueError(f"Section {i+1} must be an object")

                # Validate required fields
                if "title" not in section:
                    raise ValueError(f"Section {i+1} missing 'title' field")

                if "content" not in section:
                    raise ValueError(f"Section {i+1} missing 'content' field")

                if "sources" not in section:
                    raise ValueError(f"Section {i+1} missing 'sources' field")

                # Validate field types and content
                title = section["title"]
                if not isinstance(title, str) or not title.strip():
                    raise ValueError(f"Section {i+1} title must be a non-empty string")

                content = section["content"]
                if not isinstance(content, str) or not content.strip():
                    raise ValueError(f"Section {i+1} content must be a non-empty string")

                sources = section["sources"]
                if not isinstance(sources, list):
                    raise ValueError(f"Section {i+1} sources must be a list")

                # Validate sources
                for j, source in enumerate(sources):
                    if not isinstance(source, str) or not source.strip():
                        raise ValueError(f"Section {i+1} source {j+1} must be a non-empty string")
                    all_sources.add(source.strip())

                validated_sections.append(
                    {
                        "title": title.strip(),
                        "content": content.strip(),
                        "sources": [s.strip() for s in sources],
                    }
                )

            self.log_info(
                "Input validation successful",
                section_count=len(validated_sections),
                total_sources=len(all_sources),
            )

            return validated_sections

        except json.JSONDecodeError as e:
            self.log_error("JSON parsing failed", json_error=str(e))
            raise ValueError(f"Invalid JSON format: {str(e)}") from e
        except Exception as e:
            self.log_error("Input validation failed", exc_info=True)
            raise ValueError(f"Input validation failed: {str(e)}") from e

    def validate_output(self, output) -> str:
        """
        Validate report output format and quality.

        Args:
            output: ReActAgentRunOutput from the agent

        Returns:
            Validated and cleaned report content

        Raises:
            ValueError: If output format is invalid
        """
        # Extract text from ReActAgentRunOutput object
        output_text = output.result.text.strip()
        
        if not output_text or not output_text.strip():
            raise ValueError("Report output cannot be empty")

        output_text = output_text.strip()

        # Check length constraints
        if len(output_text) > self.max_report_length:
            self.log_warning(
                "Report exceeds maximum length",
                actual_length=len(output_text),
                max_length=self.max_report_length,
            )

        # Basic structure validation
        required_sections = ["#", "## Table of Contents", "## References"]
        for section in required_sections:
            if section not in output_text:
                self.log_warning(f"Missing expected section: {section}")

        # Count sections and references
        section_count = output_text.count("## ") - 2  # Exclude ToC and References
        reference_count = len(
            [line for line in output_text.split("\n") if line.strip().startswith("[") and "] " in line]
        )

        self.log_info(
            "Output validation completed",
            report_length=len(output_text),
            section_count=section_count,
            reference_count=reference_count,
        )

        return output_text

    def get_assembly_config(self) -> Dict[str, Any]:
        """
        Get current assembly configuration.

        Returns:
            Dictionary containing current configuration settings
        """
        return {
            "include_metadata": self.include_metadata,
            "max_report_length": self.max_report_length,
            "llm_model": self.settings.llm_model,
            "max_sections": self.settings.max_sections,
        }

    async def run_assembly(self, sections_data: str) -> str:
        """
        Run report assembly for the given sections data with comprehensive instructions.

        Args:
            sections_data: JSON string containing section data

        Returns:
            Validated assembled report content

        Raises:
            ValueError: If input/output validation fails
            RuntimeError: If assembly execution fails
        """
        try:
            # Validate input first
            validated_sections = self.validate_input(sections_data)

            self.log_info("Starting report assembly", section_count=len(validated_sections))

            # Combine instructions with the sections data
            full_prompt = f"{self.instructions}\n\nSections Data: {sections_data}"

            # Run the agent with the enhanced prompt
            raw_output = await self.agent.run(prompt=full_prompt)

            self.log_info("Report assembly completed")

            # Validate and clean the output
            validated_report = self.validate_output(raw_output)

            return validated_report

        except Exception as e:
            self.log_error("Report assembly failed", exc_info=True)
            raise RuntimeError(f"Assembly failed: {str(e)}") from e
