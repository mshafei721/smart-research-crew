from fastapi import FastAPI, Request, status, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone
from src.models import HealthResponse, SettingsResponse, ResearchRequest
from src.config.settings import get_settings
from sse_starlette.sse import EventSourceResponse
import asyncio
from src.config.logging import setup_logging, get_logger, set_request_context, clear_request_context, generate_request_id
from src.services.research_service import ResearchService

app = FastAPI()

logger = get_logger(__name__)
setup_logging()

research_service = ResearchService()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = generate_request_id()
    set_request_context(request_id)
    logger.info(f"Request: {request.method} {request.url}", extra={"request_id": request_id})
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}", extra={"request_id": request_id, "status_code": response.status_code})
    clear_request_context()
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred.", "error": str(exc)},
    )

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat(), "version": "1.0.0"}

@app.get("/settings", response_model=SettingsResponse)
def get_app_settings():
    settings = get_settings()
    return {
        "llm_model": settings.llm_model,
        "max_concurrent_tasks": settings.max_concurrent_requests,
        "cache_enabled": settings.redis_enabled,
    }

@app.post("/research")
async def submit_research_request(request: ResearchRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(research_service.conduct_research, request)
    return {"message": "Research request received", "topic": request.topic}

@app.get("/sse")
async def sse_endpoint():
    async def event_generator():
        yield {"event": "connected", "data": "Connection established"}
        await asyncio.sleep(1)
        yield {"event": "message", "data": "Processing research request..."}
        await asyncio.sleep(2)
        yield {"event": "message", "data": "Research complete!"}
        await asyncio.sleep(1)
        yield {"event": "end", "data": "Stream closed"}

    return EventSourceResponse(event_generator())


