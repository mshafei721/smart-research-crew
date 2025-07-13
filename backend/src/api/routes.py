"""
Smart Research Crew - API Routes

Production-ready API endpoints with comprehensive validation,
error handling, and observability.
"""

import asyncio
import json
from typing import List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sse_starlette.sse import EventSourceResponse

from agents import SectionResearcher, ReportAssembler
from config import get_settings
from config.logging import (
    get_logger,
    log_performance,
    set_request_context,
    generate_request_id,
)
from cache.redis_cache import get_cache
from cache.cache_integration import check_cache_health

router = APIRouter()
logger = get_logger(__name__)


class ResearchRequest(BaseModel):
    """Request model for research operations."""

    topic: str = Field(
        ..., min_length=3, max_length=200, description="Research topic to investigate"
    )
    guidelines: str = Field(
        default="",
        max_length=1000,
        description="Research guidelines, tone, and depth requirements",
    )
    sections: List[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of section titles to research",
    )

    @field_validator("sections")
    @classmethod
    def validate_sections(cls, v):
        """Validate section titles."""
        cleaned = [s.strip() for s in v if s.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty section is required")
        if len(cleaned) > 10:
            raise ValueError("Maximum 10 sections allowed")
        return cleaned

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v):
        """Validate topic."""
        if not v.strip():
            raise ValueError("Topic cannot be empty")
        return v.strip()

    @field_validator("guidelines")
    @classmethod
    def validate_guidelines(cls, v):
        """Validate guidelines."""
        return v.strip() if v else ""


class ResearchResponse(BaseModel):
    """Response model for research operations."""

    request_id: str
    status: str
    topic: str
    sections_count: int
    created_at: datetime

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    timestamp: datetime

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}


def get_current_settings():
    """Dependency to get current settings."""
    return get_settings()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health Check",
    description="Check API health status and configuration",
)
async def health_check(settings=Depends(get_current_settings)):
    """
    Health check endpoint.

    Returns application status, version, timestamp, and cache health.
    """
    logger.info("Health check requested")

    # Check cache health
    cache_health = await check_cache_health()

    response_data = {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
        "cache": cache_health,
    }

    return JSONResponse(content=response_data)


@router.get(
    "/sse",
    tags=["research"],
    summary="Stream Research Progress",
    description="""
    Server-sent events endpoint for real-time research streaming.

    Initiates a research process across multiple sections and streams:
    - Section research progress
    - Individual section completion
    - Final report assembly
    - Error handling and recovery

    The endpoint returns a stream of events with different types:
    - `status`: General progress updates
    - `section_start`: Beginning of section research
    - `section_complete`: Section research finished
    - `section_error`: Section research failed
    - `report_complete`: Final report ready
    - `error`: Critical errors

    Each event contains structured JSON data with progress information.
    """,
)
async def research_sse(
    topic: str = Query(
        ..., min_length=3, max_length=200, description="Research topic to investigate"
    ),
    guidelines: str = Query(
        default="",
        max_length=1000,
        description="Research guidelines, tone, and depth requirements",
    ),
    sections: str = Query(..., description="Comma-separated list of section titles to research"),
    settings=Depends(get_current_settings),
):
    """
    Server-sent events endpoint for streaming research progress.

    Processes research requests and streams results in real-time.
    Includes comprehensive error handling and validation.
    """
    # Generate request ID for tracking
    request_id = generate_request_id()
    set_request_context(request_id)

    # Validate input parameters
    try:
        # Parse and validate sections
        section_titles = [s.strip() for s in sections.split(",") if s.strip()]
        if not section_titles:
            raise HTTPException(status_code=400, detail="At least one section is required")
        if len(section_titles) > settings.max_sections:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {settings.max_sections} sections allowed",
            )

        # Validate topic
        if len(topic.strip()) < settings.min_topic_length:
            raise HTTPException(
                status_code=400,
                detail=f"Topic must be at least {settings.min_topic_length} characters long",
            )
        if len(topic.strip()) > settings.max_topic_length:
            raise HTTPException(
                status_code=400,
                detail=f"Topic must be less than {settings.max_topic_length} characters long",
            )

        # Validate guidelines
        if len(guidelines) > settings.max_guidelines_length:
            raise HTTPException(
                status_code=400,
                detail=f"Guidelines must be less than {settings.max_guidelines_length} characters long",
            )

        logger.info(
            "SSE research request started",
            extra={
                "request_id": request_id,
                "topic": topic,
                "section_count": len(section_titles),
                "sections": section_titles,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Request validation failed", exc_info=True, extra={"request_id": request_id})
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

    async def event_generator():
        """Generate SSE events for research progress."""
        section_results = []
        completed_sections = 0

        try:
            # Check for complete cached research result first
            cache = await get_cache()
            if cache and cache.is_connected:
                cached_research = await cache.get_cached_research_result(
                    topic, guidelines, section_titles
                )
                if cached_research:
                    logger.info(
                        "Serving cached research result",
                        extra={"request_id": request_id, "cache_hit": True},
                    )

                    # Send cached result directly
                    yield {
                        "event": "status",
                        "data": json.dumps(
                            {
                                "type": "status",
                                "message": "Retrieving cached research...",
                                "request_id": request_id,
                                "progress": 90,
                                "total_sections": len(section_titles),
                                "cache_hit": True,
                            }
                        ),
                    }

                    yield {
                        "event": "report_complete",
                        "data": json.dumps(
                            {
                                "type": "report_complete",
                                "content": cached_research,
                                "sections_completed": len(section_titles),
                                "total_sections": len(section_titles),
                                "progress": 100,
                                "cache_hit": True,
                            }
                        ),
                    }
                    return

            # Send initial status
            yield {
                "event": "status",
                "data": json.dumps(
                    {
                        "type": "status",
                        "message": "Starting research...",
                        "request_id": request_id,
                        "progress": 0,
                        "total_sections": len(section_titles),
                    }
                ),
            }

            # Process each section
            for i, title in enumerate(section_titles, 1):
                logger.info(
                    "Processing section",
                    extra={
                        "request_id": request_id,
                        "section": title,
                        "section_number": i,
                        "total_sections": len(section_titles),
                    },
                )

                try:
                    # Check for cached section result first
                    cache = await get_cache()
                    cached_section = None
                    if cache and cache.is_connected:
                        cached_section = await cache.get_cached_section_result(
                            topic, title, guidelines
                        )

                    if cached_section:
                        # Use cached section result
                        section_result = {"title": title, **cached_section}
                        section_results.append(section_result)
                        completed_sections += 1

                        logger.info(
                            "Using cached section result",
                            extra={
                                "request_id": request_id,
                                "section": title,
                                "cache_hit": True,
                            },
                        )

                        # Send section completion event for cached result
                        yield {
                            "event": "section_complete",
                            "data": json.dumps(
                                {
                                    "type": "section_complete",
                                    "section": title,
                                    "content": section_result.get("content", ""),
                                    "sources": section_result.get("sources", []),
                                    "format": "json",
                                    "progress": (i / len(section_titles)) * 80,  # 80% for sections
                                    "cache_hit": True,
                                }
                            ),
                        }

                    else:
                        # Send section start event
                        yield {
                            "event": "section_start",
                            "data": json.dumps(
                                {
                                    "type": "section_start",
                                    "section": title,
                                    "section_number": i,
                                    "total_sections": len(section_titles),
                                    "progress": (i - 1) / len(section_titles) * 100,
                                }
                            ),
                        }

                        with log_performance(f"research_section_{i}", logger):
                            # Create and run agent with timeout
                            researcher = SectionResearcher(title, guidelines)

                            result = await asyncio.wait_for(
                                researcher.run_research(
                                    f"Research section '{title}' on topic: {topic}"
                                ),
                                timeout=settings.section_timeout,
                            )

                            # The new run_research method returns validated data
                            section_result = {"title": title, **result}
                            format_type = "json"

                            section_results.append(section_result)
                            completed_sections += 1

                            # Cache the section result
                            if cache and cache.is_connected:
                                await cache.cache_section_result(topic, title, guidelines, result)

                            # Send section completion event
                            yield {
                                "event": "section_complete",
                                "data": json.dumps(
                                    {
                                        "type": "section_complete",
                                        "section": title,
                                        "content": section_result.get("content", ""),
                                        "sources": section_result.get("sources", []),
                                        "format": format_type,
                                        "progress": (i / len(section_titles))
                                        * 80,  # 80% for sections
                                    }
                                ),
                            }

                            logger.info(
                                "Section completed",
                                extra={
                                    "request_id": request_id,
                                    "section": title,
                                    "format": format_type,
                                },
                            )

                except asyncio.TimeoutError:
                    error_msg = f"Section research timeout after {settings.section_timeout}s"
                    logger.error(
                        "Section research timeout",
                        extra={
                            "request_id": request_id,
                            "section": title,
                            "timeout": settings.section_timeout,
                        },
                    )

                    section_results.append(
                        {
                            "title": title,
                            "content": f"Error: {error_msg}",
                            "sources": [],
                        }
                    )

                    yield {
                        "event": "section_error",
                        "data": json.dumps(
                            {
                                "type": "section_error",
                                "section": title,
                                "error": error_msg,
                                "progress": (i / len(section_titles)) * 80,
                            }
                        ),
                    }

                except Exception as e:
                    error_msg = f"Section research failed: {str(e)}"
                    logger.error(
                        "Section research failed",
                        exc_info=True,
                        extra={
                            "request_id": request_id,
                            "section": title,
                        },
                    )

                    section_results.append(
                        {
                            "title": title,
                            "content": f"Error: {error_msg}",
                            "sources": [],
                        }
                    )

                    yield {
                        "event": "section_error",
                        "data": json.dumps(
                            {
                                "type": "section_error",
                                "section": title,
                                "error": error_msg,
                                "progress": (i / len(section_titles)) * 80,
                            }
                        ),
                    }

                # Small delay between sections
                await asyncio.sleep(0.1)

            # Assemble final report
            yield {
                "event": "status",
                "data": json.dumps(
                    {
                        "type": "status",
                        "message": "Assembling final report...",
                        "progress": 80,
                    }
                ),
            }

            try:
                with log_performance("assemble_report", logger):
                    assembler = ReportAssembler()

                    report = await asyncio.wait_for(
                        assembler.run_assembly(json.dumps(section_results)),
                        timeout=settings.request_timeout,
                    )

                    # Cache the complete research result
                    cache = await get_cache()
                    if cache and cache.is_connected:
                        await cache.cache_research_result(topic, guidelines, section_titles, report)

                    yield {
                        "event": "report_complete",
                        "data": json.dumps(
                            {
                                "type": "report_complete",
                                "content": report,
                                "sections_completed": completed_sections,
                                "total_sections": len(section_titles),
                                "progress": 100,
                            }
                        ),
                    }

                    logger.info(
                        "Research completed successfully",
                        extra={
                            "request_id": request_id,
                            "sections_completed": completed_sections,
                            "total_sections": len(section_titles),
                        },
                    )

            except asyncio.TimeoutError:
                error_msg = f"Report assembly timeout after {settings.request_timeout}s"
                logger.error(
                    "Report assembly timeout",
                    extra={
                        "request_id": request_id,
                        "timeout": settings.request_timeout,
                    },
                )

                yield {
                    "event": "error",
                    "data": json.dumps({"type": "error", "message": error_msg, "progress": 80}),
                }

            except Exception as e:
                error_msg = f"Report assembly failed: {str(e)}"
                logger.error(
                    "Report assembly failed",
                    exc_info=True,
                    extra={"request_id": request_id},
                )

                yield {
                    "event": "error",
                    "data": json.dumps({"type": "error", "message": error_msg, "progress": 80}),
                }

        except Exception as e:
            logger.error(
                "SSE event generation failed",
                exc_info=True,
                extra={"request_id": request_id},
            )

            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "type": "error",
                        "message": f"Research failed: {str(e)}",
                        "progress": 0,
                    }
                ),
            }

    return EventSourceResponse(event_generator())
