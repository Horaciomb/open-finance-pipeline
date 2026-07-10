"""Decorador de reintentos con backoff exponencial para llamadas a APIs externas."""

import functools
import logging
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)


def retry_with_backoff(max_attempts: int = 3, base_delay: float = 1.0):
    """Reintenta una función ante cualquier excepción, con backoff exponencial.

    Args:
        max_attempts: número máximo de intentos (incluyendo el primero).
        base_delay: segundos de espera tras el primer fallo; se duplica en cada reintento.
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    if attempt == max_attempts:
                        break
                    logger.warning(
                        "Intento %d/%d falló para %s: %s. Reintentando en %.1fs",
                        attempt,
                        max_attempts,
                        func.__name__,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
                    delay *= 2
            raise last_exc

        return wrapper

    return decorator
