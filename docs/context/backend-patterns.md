# Backend Patterns Cheat-Sheet

- **Entrypoint**: `main.py` (unified CLI & Server modes)
- **CLI Mode**: `python main.py` (interactive research)
- **Server Mode**: `python main.py --server` (FastAPI :8000)
- Agents inherit from `beeai_framework.agents.react.ReActAgent`
- Return type: `{"content": str, "sources": List[dict]}`
- Search tools:
  - DuckDuckGoSearchTool (default)
  - ArXivSearchTool (future)
- Error handling:
  ```python
  try:
      ...
  except Exception as e:
      return {"content": f"Error: {e}", "sources": []}
  ```
- **SSE endpoint**: GET /sse uses sse-starlette (real-time streaming)
- **Caching**: Redis layer with TTL management (`backend/src/cache/`)
- **Configuration**: Environment-based settings (`backend/src/config/`)
- **Logging**: structlog JSON to stdout
- **Testing**: Unit tests in `backend/tests/`, E2E in `tests/e2e/`
