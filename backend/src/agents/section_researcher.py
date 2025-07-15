"""
Smart Research Crew - Section Researcher Agent

Intelligent agent responsible for researching individual report sections
with web search capabilities and structured JSON output.
"""

import textwrap
from typing import Dict, Any
import asyncio

from beeai_framework.agents.react import ReActAgent
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.backend.chat import ChatModel
from src.memory.redis_memory import RedisMemory

from src.config.settings import get_settings
from src.config.logging import LoggerMixin

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


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
        >>> researcher = SectionResearcher("Introduction",
        ...                                "Academic tone, focus on recent developments")
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
                memory=RedisMemory(session_id=f"section_researcher_{self.section}", ttl=self.settings.cache_section_ttl),
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
            1. Search the web for {self.max_sources} high-quality, recent, and credible sources relevant to "{self.section}".
            2. Analyze the gathered information to synthesize comprehensive and well-structured content for the section.
            3. Write the content in Markdown format, ensuring it does not exceed {self.max_content_words} words.
            4. For every piece of information or statistic, include proper citations using the format [1], [2], [3], etc., corresponding to the order of sources in the "sources" list.
            5. If no relevant information is found after thorough searching, return an empty content string and an empty sources list: {{\"content\": \"\", \"sources\": []}}.

            CONTENT QUALITY REQUIREMENTS:
            - Use clear, concise, and professional language.
            - Employ proper Markdown formatting (e.g., headers, bullet points, bold/italic text) to enhance readability.
            - Include specific facts, figures, and examples to support claims.
            - Maintain academic rigor and factual accuracy.
            - Ensure all claims are backed by cited sources.
            - Prioritize recent information (ideally from the last 2-3 years) from credible sources.

            SOURCE QUALITY REQUIREMENTS:
            - Prioritize authoritative and reputable sources (e.g., .edu, .gov, well-known research institutions, established news organizations).
            - Include a diverse range of sources to provide a balanced perspective.
            - Verify that all URLs are accessible and directly relevant to the content.
            - Avoid blogs, opinion pieces, or unreliable sources unless explicitly necessary and noted.

            OUTPUT CONSTRAINTS:
            - Return ONLY the JSON object - no additional text, explanations, or formatting outside the JSON.
            - The JSON MUST be valid and parseable.
            - Ensure proper JSON escaping for all quotes and special characters within the "content" field.
            - The total length of the JSON output should be reasonable, considering the content and source limits.

            EXAMPLE OUTPUT (for a section on "Introduction to AI"):
            {{"content": "## Introduction to Artificial Intelligence\n\nArtificial Intelligence (AI) is a rapidly evolving field that aims to create machines capable of performing tasks that typically require human intelligence [1]. This includes learning, problem-solving, perception, and language understanding. Recent advancements in deep learning and neural networks have significantly propelled AI capabilities, leading to breakthroughs in various sectors [2].\n\n### Historical Context\n\nThe concept of AI dates back to the 1950s, with early pioneers like Alan Turing exploring the theoretical foundations of intelligent machines [3]. The field has experienced periods of rapid growth and stagnation, often referred to as 'AI winters,' but current progress suggests a sustained period of innovation [4].", "sources": ["https://example.edu/ai-intro", "https://techcrunch.com/ai-breakthroughs", "https://historyofai.org/turing", "https://ai-research.net/ai-winters"]}}
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

    def validate_output(self, output) -> Dict[str, Any]:
        """
        Validate agent output format and content.

        Args:
            output: ReActAgentRunOutput from the agent or string for testing

        Returns:
            Parsed and validated JSON data

        Raises:
            ValueError: If output format is invalid
        """
        import json

        try:
            # Handle both BeeAI output objects and test mocks (strings)
            if hasattr(output, "result") and hasattr(output.result, "text"):
                # Real BeeAI output object
                output_text = output.result.text.strip()
            elif isinstance(output, str):
                # Test mock string
                output_text = output.strip()
            else:
                # Fallback - try to convert to string
                output_text = str(output).strip()

            data = json.loads(output_text)

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
        Run research for the given query with comprehensive instructions and retry logic.

        Args:
            query: The research query/topic

        Returns:
            Parsed and validated research results

        Raises:
            ValueError: If output validation fails after all retries
            RuntimeError: If research execution fails after all retries
        """
        for attempt in range(MAX_RETRIES):
            try:
                self.log_info("Starting research", query=query, section=self.section, attempt=attempt + 1)
                full_prompt = f"{self.instructions}\n\nResearch Query: {query}"
                raw_output = await self.agent.run(prompt=full_prompt)
                validated_data = self.validate_output(raw_output)
                self.log_info("Research completed", section=self.section, attempt=attempt + 1)
                return validated_data
            except Exception as e:
                self.log_error(
                    f"Research execution failed on attempt {attempt + 1}",
                    exc_info=True,
                    query=query,
                )
                if attempt < MAX_RETRIES - 1:
                    self.log_warning(f"Retrying in {RETRY_DELAY} seconds...")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    raise RuntimeError(f"Research failed after {MAX_RETRIES} attempts: {str(e)}") from e
