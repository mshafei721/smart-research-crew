from fastapi import FastAPI, Request, status, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone
from src.models import HealthResponse, SettingsResponse, ResearchRequest
from src.config.settings import get_settings
from sse_starlette.sse import EventSourceResponse
import asyncio
from src.config.logging import setup_logging, get_logger, set_request_context, clear_request_context, generate_request_id
from src.services.research_service import ResearchService
import uuid
from typing import Dict
import json
from src.database import get_redis_connection

app = FastAPI()

logger = get_logger(__name__)
setup_logging()

research_service = ResearchService()

# Redis client for task state persistence
redis_client = get_redis_connection()

# In-memory cache for active research tasks to reduce Redis hits
active_research_tasks: Dict[str, ResearchRequest] = {}

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
async def submit_research_request(request: ResearchRequest):
    task_id = str(uuid.uuid4())
    if redis_client:
        redis_client.set(f"research_task:{task_id}", request.json())
        redis_client.expire(f"research_task:{task_id}", 3600) # Expire after 1 hour
    else:
        # Fallback to in-memory if Redis is not available
        active_research_tasks[task_id] = request

    logger.info(f"Research request received: {request.topic}", extra={"task_id": task_id})
    return {"message": "Research request received", "task_id": task_id}

@app.get("/sse")
async def sse_endpoint(task_id: str):
    research_request = None
    if redis_client:
        task_data = redis_client.get(f"research_task:{task_id}")
        if task_data:
            research_request = ResearchRequest.parse_raw(task_data)
    
    if not research_request and task_id in active_research_tasks:
        research_request = active_research_tasks[task_id]

    if not research_request:
        raise HTTPException(status_code=404, detail="Task ID not found")

    async def event_generator():
        try:
            async for event in research_service.conduct_research(research_request):
                yield json.dumps(event)
        except Exception as e:
            logger.error(f"Error during SSE stream for task {task_id}: {e}", exc_info=True)
            yield json.dumps({"event": "error", "data": str(e)})
        finally:
            # Clean up the task after completion or error
            if redis_client:
                redis_client.delete(f"research_task:{task_id}")
            elif task_id in active_research_tasks:
                del active_research_tasks[task_id]
            logger.info(f"Cleaned up task {task_id}")

    return EventSourceResponse(event_generator())


