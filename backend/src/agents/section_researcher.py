"""
Smart Research Crew - Section Researcher Agent

Intelligent agent responsible for researching individual report sections
with web search capabilities and structured JSON output.
"""

import textwrap
from typing import Dict, List, Any, Optional

from beeai_framework.agents.react import ReActAgent
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.backend.chat import ChatModel
from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory

from config import get_settings
from config.logging import LoggerMixin, get_logger


class SectionResearcher(LoggerMixin):
    """
    Agent responsible for researching individual report sections.

    This agent uses web search capabilities to gather information on a specific
    section topic and returns structured JSON with content and source citations.

    Attributes:
        section (str): The section title to research
        guidelines (str): User-provided research guidelines and tone requirements
        agent (ReActAgent): The underlying BeeAI agent instance
        settings: Application settings for configuration

    Returns:
        JSON object with structured content:
        {
            "content": "Markdown formatted section content",
            "sources": ["url1", "url2", "url3"]
        }

    Example:
        >>> researcher = SectionResearcher("Introduction", "Academic tone, focus on recent developments")
        >>> result = await researcher.agent.run("Research AI developments")
        >>> data = json.loads(result)
        >>> print(data["content"])
    """

    def __init__(
        self, section: str, guidelines: str, max_sources: int = 5, max_content_words: int = 250
    ):
        """
        Initialize the Section Researcher agent.

        Args:
            section: The section title to research
            guidelines: User-provided research guidelines and tone
            max_sources: Maximum number of sources to include (default: 5)
            max_content_words: Maximum words in content (default: 250)

        Raises:
            ValueError: If section or guidelines are invalid
        """
        if not section or not section.strip():
            raise ValueError("Section title cannot be empty")

        if len(section) > 100:
            raise ValueError("Section title must be less than 100 characters")

        if len(guidelines) > 1000:
            raise ValueError("Guidelines must be less than 1000 characters")

        self.section = section.strip()
        self.guidelines = guidelines.strip() if guidelines else ""
        self.max_sources = max_sources
        self.max_content_words = max_content_words
        self.settings = get_settings()

        self.log_info(
            "Initializing SectionResearcher",
            section=self.section,
            guidelines_length=len(self.guidelines),
            max_sources=max_sources,
            max_content_words=max_content_words,
        )

        # Store instructions for later use in run-time prompts
        self.instructions = self._create_instructions()

        # Initialize the agent with configured model (no instructions parameter)
        try:
            self.agent = ReActAgent(
                llm=ChatModel.from_name(self.settings.llm_model),
                tools=[DuckDuckGoSearchTool()],
                memory=UnconstrainedMemory(),
            )

            self.log_info("SectionResearcher initialized successfully")

        except Exception as e:
            self.log_error("Failed to initialize SectionResearcher", exc_info=True)
            raise RuntimeError(f"Agent initialization failed: {str(e)}") from e

    def _create_instructions(self) -> str:
        """
        Create detailed instructions for the research agent.

        Returns:
            Formatted instruction string for the agent
        """
        guidelines_text = (
            f"\nGuidelines from the user: {self.guidelines}" if self.guidelines else ""
        )

        instructions = textwrap.dedent(
            f"""
            You are a specialized research agent responsible ONLY for the section "{self.section}".
            {guidelines_text}
            
            CRITICAL OUTPUT FORMAT REQUIREMENTS:
            You MUST return ONLY valid JSON in this EXACT format:
            {{"content": "your markdown content here", "sources": ["url1", "url2", "url3"]}}
            
            RESEARCH PROCESS:
            1. Search the web for {self.max_sources} high-quality, recent, and credible sources
            2. Analyze the information to create comprehensive section content
            3. Write well-structured Markdown content (maximum {self.max_content_words} words)
            4. Include proper citations using [1], [2], [3] format within the content
            5. Return structured JSON with content and source URLs
            
            CONTENT QUALITY REQUIREMENTS:
            - Use proper Markdown formatting (headers, lists, emphasis)
            - Include specific facts, statistics, and examples where relevant
            - Maintain academic rigor and factual accuracy
            - Ensure citations are properly integrated into the text
            - Focus on recent information (prefer sources from last 2-3 years)
            
            SOURCE QUALITY REQUIREMENTS:
            - Prioritize authoritative sources (.edu, .gov, reputable organizations)
            - Include diverse perspectives and up-to-date information
            - Avoid low-quality or unreliable sources
            - Ensure URLs are accessible and relevant
            
            OUTPUT CONSTRAINTS:
            - Return ONLY the JSON object - no additional text, explanations, or formatting
            - The JSON must be valid and parseable
            - Do not include any text before or after the JSON
            - Ensure proper JSON escaping for quotes and special characters
            - Maximum {len(self.guidelines) + 500} characters for guidelines consideration
            
            EXAMPLE OUTPUT:
            {{"content": "## Key Findings\\n\\nRecent research shows [1] that artificial intelligence adoption has increased by 45% in 2023 [2]. This trend indicates...\\n\\n### Impact Analysis\\n\\n- **Efficiency**: 60% improvement in processing time [3]\\n- **Cost**: Average reduction of $50k annually [1]", "sources": ["https://example.edu/ai-research-2023", "https://techreport.org/ai-adoption-trends", "https://industry-analysis.com/efficiency-study"]}}
        """
        )

        return instructions

    def get_research_config(self) -> Dict[str, Any]:
        """
        Get current research configuration.

        Returns:
            Dictionary containing current configuration settings
        """
        return {
            "section": self.section,
            "guidelines": self.guidelines,
            "max_sources": self.max_sources,
            "max_content_words": self.max_content_words,
            "llm_model": self.settings.llm_model,
            "search_timeout": self.settings.search_timeout,
        }

    def validate_output(self, output: str) -> Dict[str, Any]:
        """
        Validate agent output format and content.

        Args:
            output: Raw output from the agent

        Returns:
            Parsed and validated JSON data

        Raises:
            ValueError: If output format is invalid
        """
        import json

        try:
            data = json.loads(output.strip())

            # Validate required fields
            if not isinstance(data, dict):
                raise ValueError("Output must be a JSON object")

            if "content" not in data:
                raise ValueError("Missing required 'content' field")

            if "sources" not in data:
                raise ValueError("Missing required 'sources' field")

            if not isinstance(data["sources"], list):
                raise ValueError("'sources' field must be a list")

            # Validate content
            content = data["content"]
            if not content or not content.strip():
                raise ValueError("Content cannot be empty")

            word_count = len(content.split())
            if word_count > self.max_content_words:
                self.log_warning(
                    "Content exceeds word limit",
                    word_count=word_count,
                    max_words=self.max_content_words,
                )

            # Validate sources
            sources = data["sources"]
            if len(sources) > self.max_sources:
                self.log_warning(
                    "Too many sources provided",
                    source_count=len(sources),
                    max_sources=self.max_sources,
                )

            for i, source in enumerate(sources):
                if not isinstance(source, str) or not source.strip():
                    raise ValueError(f"Source {i+1} must be a non-empty string")

            self.log_info(
                "Output validation successful", word_count=word_count, source_count=len(sources)
            )

            return data

        except json.JSONDecodeError as e:
            self.log_error("JSON parsing failed", json_error=str(e))
            raise ValueError(f"Invalid JSON format: {str(e)}") from e
        except Exception as e:
            self.log_error("Output validation failed", exc_info=True)
            raise ValueError(f"Output validation failed: {str(e)}") from e

    async def run_research(self, query: str) -> Dict[str, Any]:
        """
        Run research for the given query with comprehensive instructions.

        Args:
            query: The research query/topic

        Returns:
            Parsed and validated research results

        Raises:
            ValueError: If output validation fails
            RuntimeError: If research execution fails
        """
        try:
            # Combine instructions with the user query
            full_prompt = f"{self.instructions}\n\nResearch Query: {query}"

            self.log_info("Starting research", query=query, section=self.section)

            # Run the agent with the enhanced prompt
            raw_output = await self.agent.run(prompt=full_prompt)

            self.log_info("Research completed", section=self.section)

            # Validate and parse the output
            validated_data = self.validate_output(raw_output)

            return validated_data

        except Exception as e:
            self.log_error("Research execution failed", exc_info=True, query=query)
            raise RuntimeError(f"Research failed: {str(e)}") from e
