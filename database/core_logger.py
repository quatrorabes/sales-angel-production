"""
Structured logging with JSON output and Sentry integration
"""

import logging
import structlog
import sys
from datetime import datetime
from typing import Any, Dict

def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance

    Args:
        name: Module name (usually __name__)

    Returns:
        Configured structlog logger
    """

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Get logger
    logger = structlog.get_logger(name)

    return logger


class PerformanceLogger:
    """Context manager for logging performance metrics"""

    def __init__(self, logger: structlog.BoundLogger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type is None:
            self.logger.info(
                f"Completed: {self.operation}",
                duration_seconds=duration,
                success=True
            )
        else:
            self.logger.error(
                f"Failed: {self.operation}",
                duration_seconds=duration,
                success=False,
                error=str(exc_val)
            )

        return False  # Don't suppress exceptions
