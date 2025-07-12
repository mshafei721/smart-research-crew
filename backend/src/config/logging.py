"""
Smart Research Crew - Logging Configuration

Structured logging setup with request tracing and performance monitoring.
"""

import logging
import sys
import uuid
from typing import Dict, Any, Optional
from contextvars import ContextVar
from datetime import datetime

try:
    from .settings import get_settings
except ImportError:
    # Handle case when imported directly
    def get_settings():
        class DummySettings:
            log_level = "INFO"
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            debug = False
            enable_request_logging = True

        return DummySettings()


# Context variables for request tracing
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class RequestContextFilter(logging.Filter):
    """Add request context to log records."""

    def filter(self, record):
        """Add context variables to log record."""
        record.request_id = request_id_var.get() or "no-request"
        record.user_id = user_id_var.get() or "anonymous"
        return True


class StructuredFormatter(logging.Formatter):
    """Structured logging formatter with JSON-like output."""

    def format(self, record):
        """Format log record with structured data."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "no-request"),
            "user_id": getattr(record, "user_id", "anonymous"),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "request_id",
                "user_id",
            ]:
                log_data["extra_" + key] = value

        return str(log_data)


def setup_logging():
    """Configure application logging with structured output."""
    settings = get_settings()

    # Remove default handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Configure root logger
    root_logger.setLevel(getattr(logging, settings.log_level))

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level))

    # Choose formatter based on debug mode
    if settings.debug:
        # Simple format for development
        formatter = logging.Formatter(settings.log_format)
    else:
        # Structured format for production
        formatter = StructuredFormatter()

    console_handler.setFormatter(formatter)

    # Add request context filter
    console_handler.addFilter(RequestContextFilter())

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    configure_library_loggers()

    return root_logger


def configure_library_loggers():
    """Configure logging for third-party libraries."""
    # Reduce noise from common libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    # Enable request logging if configured
    settings = get_settings()
    if settings.enable_request_logging:
        logging.getLogger("uvicorn.access").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def set_request_context(request_id: str, user_id: Optional[str] = None):
    """Set request context for logging."""
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context():
    """Clear request context."""
    request_id_var.set(None)
    user_id_var.set(None)


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


class LoggerMixin:
    """Mixin class to add logging capabilities to other classes."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    def log_info(self, message: str, **kwargs):
        """Log info message with extra context."""
        self.logger.info(message, extra=kwargs)

    def log_warning(self, message: str, **kwargs):
        """Log warning message with extra context."""
        self.logger.warning(message, extra=kwargs)

    def log_error(self, message: str, exc_info=None, **kwargs):
        """Log error message with extra context."""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)

    def log_debug(self, message: str, **kwargs):
        """Log debug message with extra context."""
        self.logger.debug(message, extra=kwargs)


# Performance monitoring helpers
class PerformanceLogger:
    """Logger for performance monitoring."""

    def __init__(self, operation: str, logger: logging.Logger):
        self.operation = operation
        self.logger = logger
        self.start_time = None

    def __enter__(self):
        """Start timing operation."""
        self.start_time = datetime.utcnow()
        self.logger.debug(f"Starting operation: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log operation completion time."""
        if self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds()
            if exc_type:
                self.logger.error(
                    f"Operation failed: {self.operation}",
                    extra={"duration_seconds": duration, "error": str(exc_val)},
                )
            else:
                self.logger.info(
                    f"Operation completed: {self.operation}", extra={"duration_seconds": duration}
                )


def log_performance(operation: str, logger: Optional[logging.Logger] = None):
    """Context manager for performance logging."""
    if logger is None:
        logger = logging.getLogger(__name__)
    return PerformanceLogger(operation, logger)
