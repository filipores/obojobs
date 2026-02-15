"""Centralized retry utility with exponential backoff."""

import logging
import random
import time
from functools import wraps

logger = logging.getLogger(__name__)


def retry_with_backoff(max_attempts=3, base_delay=2.0, max_delay=30.0, exceptions=(Exception,)):
    """Decorator for retrying functions with exponential backoff and jitter.

    Args:
        max_attempts: Maximum number of attempts (must be >= 1).
        base_delay: Base delay in seconds (doubled each retry).
        max_delay: Maximum delay cap in seconds.
        exceptions: Tuple of exception types to catch and retry on.

    Raises:
        The last caught exception after all attempts are exhausted.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    is_last_attempt = attempt >= max_attempts - 1
                    if is_last_attempt:
                        break
                    delay = min(base_delay * (2**attempt) + random.uniform(0, 1), max_delay)
                    logger.warning(
                        "%s fehlgeschlagen (Versuch %d/%d): %s. Retry in %.1fs",
                        func.__name__,
                        attempt + 1,
                        max_attempts,
                        e,
                        delay,
                    )
                    time.sleep(delay)
            raise last_exception

        return wrapper

    return decorator
