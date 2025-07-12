#!/usr/bin/env python3
"""
Smart Research Crew - Main application entry point.

Production-ready application with proper configuration management,
structured logging, and comprehensive error handling.
Can be run as CLI or FastAPI server.
"""
import asyncio
import sys
import os
import json
from typing import List

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from rich.console import Console
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import configuration and logging
from config import settings, get_settings, validate_environment
from config.logging import (
    setup_logging,
    get_logger,
    set_request_context,
    generate_request_id,
    log_performance,
)

# Import application modules
from agents import SectionResearcher, ReportAssembler
from api import router
from utils import ask
from cache.cache_integration import cache_lifespan, CacheMiddleware, add_cache_routes

# Initialize logging
logger = setup_logging()
app_logger = get_logger(__name__)

# Validate environment on startup
if not validate_environment():
    app_logger.error("Environment validation failed. Please check your configuration.")
    sys.exit(1)

console = Console()

# FastAPI app setup with configuration
app_settings = get_settings()
app = FastAPI(
    title=app_settings.app_name,
    version=app_settings.app_version,
    description="""
    Smart Research Crew API - Intelligent research automation platform
    
    This API provides endpoints for automated research using AI agents that can:
    - Research multiple sections of a topic in parallel
    - Gather information from web sources
    - Generate structured reports with citations
    - Stream research progress in real-time
    - Cache results using Redis for improved performance
    
    ## Authentication
    Currently no authentication required for development.
    
    ## Rate Limiting
    Rate limiting can be enabled via environment variables.
    
    ## Caching
    Redis caching can be enabled via REDIS_ENABLED environment variable.
    
    ## Monitoring
    Request tracing and structured logging available.
    """,
    debug=app_settings.debug,
    contact={
        "name": "Smart Research Crew Team",
        "url": "https://github.com/your-org/smart-research-crew",
        "email": "support@smartresearchcrew.com",
    },
    license_info={"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
    openapi_tags=[
        {"name": "research", "description": "Research operations and streaming endpoints"},
        {"name": "health", "description": "Health check and monitoring endpoints"},
        {"name": "cache", "description": "Cache management and monitoring endpoints"},
        {"name": "system", "description": "System information and configuration"},
    ],
    lifespan=cache_lifespan,
)

# CORS middleware with configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_methods=app_settings.cors_methods,
    allow_headers=app_settings.cors_headers,
    allow_credentials=True,
)

# Cache middleware
app.add_middleware(CacheMiddleware, add_cache_headers=True)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing and context."""
    request_id = generate_request_id()
    set_request_context(request_id)

    with log_performance(f"{request.method} {request.url.path}", app_logger):
        app_logger.info(
            "Request received",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_host=request.client.host if request.client else "unknown",
        )

        try:
            response = await call_next(request)
            app_logger.info("Request completed", status_code=response.status_code)
            return response
        except Exception as e:
            app_logger.error(
                "Request failed", exc_info=True, error_type=type(e).__name__, error_message=str(e)
            )
            raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions."""
    app_logger.error(
        "Unhandled exception occurred", exc_info=True, path=request.url.path, method=request.method
    )

    if app_settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc),
                "type": type(exc).__name__,
            },
        )
    else:
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


# Include API routes
app.include_router(router)

# Add cache management routes
add_cache_routes(app)


async def run_cli_mode():
    """
    Run the research crew in CLI mode with proper validation and error handling.
    """
    console.print("\n[bold magenta]=== Smart Research Crew ===[/bold magenta]\n")
    app_logger.info("Starting CLI mode")

    try:
        # Get input with validation
        topic = ask("📌  Research topic: ").strip()
        if len(topic) < app_settings.min_topic_length:
            console.print(
                f"[red]Topic must be at least {app_settings.min_topic_length} characters long[/red]"
            )
            return
        if len(topic) > app_settings.max_topic_length:
            console.print(
                f"[red]Topic must be less than {app_settings.max_topic_length} characters long[/red]"
            )
            return

        guide = ask("🧭  Guidelines / tone / depth: ").strip()
        if len(guide) > app_settings.max_guidelines_length:
            console.print(
                f"[red]Guidelines must be less than {app_settings.max_guidelines_length} characters long[/red]"
            )
            return

        sections_input = ask("🗂️   Desired sections (comma separated): ").strip()
        sections = [s.strip() for s in sections_input.split(",") if s.strip()]

        if len(sections) == 0:
            console.print("[red]At least one section is required[/red]")
            return
        if len(sections) > app_settings.max_sections:
            console.print(f"[red]Maximum {app_settings.max_sections} sections allowed[/red]")
            return

        app_logger.info(
            f"CLI research started: topic='{topic}', section_count={len(sections)}, sections={sections}"
        )

        console.print(f"\n🚀  Spinning up agents for {len(sections)} sections…\n")

        # Process sections sequentially for CLI mode
        section_results = []
        for i, sec in enumerate(sections, 1):
            console.print(f"[dim]• Researching section {i}/{len(sections)}: {sec}...[/dim]")

            with log_performance(f"research_section_{i}", app_logger):
                try:
                    researcher = SectionResearcher(sec, guide)

                    result = await asyncio.wait_for(
                        researcher.run_research(f"Research section '{sec}' on topic: {topic}"),
                        timeout=app_settings.section_timeout,
                    )

                    # The new run_research method returns validated data
                    section_results.append({"title": sec, **result})
                    app_logger.info(f"Section research completed: {sec} (format=json)")

                except asyncio.TimeoutError:
                    error_msg = f"Timeout after {app_settings.section_timeout}s"
                    console.print(f"[red]Timeout researching {sec}: {error_msg}[/red]")
                    app_logger.error(
                        f"Section research timeout: section='{sec}', timeout={app_settings.section_timeout}s"
                    )
                    section_results.append(
                        {"title": sec, "content": f"Error: {error_msg}", "sources": []}
                    )
                except Exception as e:
                    console.print(f"[red]Error researching {sec}: {e}[/red]")
                    app_logger.error(f"Section research failed: section='{sec}'", exc_info=True)
                    section_results.append({"title": sec, "content": f"Error: {e}", "sources": []})

        # Assemble final report
        console.print("\n[dim]• Assembling final report...[/dim]")

        with log_performance("assemble_report", app_logger):
            assembler = ReportAssembler()
            try:
                report = await asyncio.wait_for(
                    assembler.run_assembly(json.dumps(section_results)),
                    timeout=app_settings.request_timeout,
                )
                console.print("\n[bold green]Report ready 🎉[/bold green]\n")
                console.print(report)
                app_logger.info("CLI research completed successfully")
            except asyncio.TimeoutError:
                console.print(
                    f"[red]Timeout assembling report after {app_settings.request_timeout}s[/red]"
                )
                app_logger.error(
                    f"Report assembly timeout: timeout={app_settings.request_timeout}s"
                )
            except Exception as e:
                console.print(f"[red]Error assembling report: {e}[/red]")
                app_logger.error("Report assembly failed", exc_info=True)

    except KeyboardInterrupt:
        console.print("\n[yellow]Research interrupted by user[/yellow]")
        app_logger.info("CLI research interrupted by user")
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        app_logger.error("CLI research failed with unexpected error", exc_info=True)


def main():
    """
    Main entry point with improved argument handling and configuration.
    """
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] == "--server":
                # Start FastAPI server with configuration
                app_logger.info(
                    f"Starting FastAPI server at {app_settings.host}:{app_settings.port} "
                    f"(reload={app_settings.reload}, debug={app_settings.debug})"
                )
                uvicorn.run(
                    "crew:app",
                    host=app_settings.host,
                    port=app_settings.port,
                    reload=app_settings.reload,
                    log_level=app_settings.log_level.lower(),
                )
            elif sys.argv[1] == "--validate":
                # Validate configuration and environment
                if validate_environment():
                    console.print("[green]✅ Configuration validation passed[/green]")
                    app_logger.info("Configuration validation successful")
                else:
                    console.print("[red]❌ Configuration validation failed[/red]")
                    app_logger.error("Configuration validation failed")
                    sys.exit(1)
            elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
                # Show help
                console.print(
                    """
[bold magenta]Smart Research Crew[/bold magenta]

Usage:
  python crew.py                 - Interactive CLI mode
  python crew.py --server        - Start FastAPI server
  python crew.py --validate      - Validate configuration
  python crew.py --help          - Show this help

Environment Variables:
  OPENAI_API_KEY                 - Required: OpenAI API key
  LLM_MODEL                      - Optional: LLM model name (default: openai)
  PORT                           - Optional: Server port (default: 8000)
  DEBUG                          - Optional: Enable debug mode (default: false)
  LOG_LEVEL                      - Optional: Log level (default: INFO)

For more configuration options, see .env.example
                """
                )
            else:
                # Invalid argument
                console.print(f"[red]Unknown argument: {sys.argv[1]}[/red]")
                console.print("Use --help for usage information")
                sys.exit(1)
        else:
            # Interactive CLI mode
            console.print(
                f"[dim]Using configuration: LLM={app_settings.llm_model}, Max Sections={app_settings.max_sections}[/dim]"
            )
            asyncio.run(run_cli_mode())

    except KeyboardInterrupt:
        console.print("\n[yellow]Application interrupted by user[/yellow]")
        app_logger.info("Application interrupted by user")
    except Exception as e:
        console.print(f"\n[red]Application startup failed: {e}[/red]")
        app_logger.error("Application startup failed", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
