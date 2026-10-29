"""Circuit breaker (3 estados), retry con backoff exponencial y cliente HTTP que los usa."""
import json
import logging
import time
from enum import Enum
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.domain.errors import CircuitOpen, UpstreamFailure

logger = logging.getLogger(__name__)


class TransientError(Exception):
    """Fallo temporal (sin red, timeout, 5xx, 429): se reintenta."""


class PermanentError(Exception):
    """Fallo definitivo (404, JSON inválido): no se reintenta."""


class CircuitOpenError(Exception):
    pass


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(self, name, failure_threshold=3, recovery_timeout=30.0, clock=time.monotonic):
        self.name = name
        self._threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._clock = clock
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._opened_at = 0.0

    @property
    def state(self) -> CircuitState:
        # OPEN pasa solo a HALF_OPEN cuando termina el tiempo de espera.
        if (self._state is CircuitState.OPEN
                and self._clock() - self._opened_at >= self._recovery_timeout):
            self._state = CircuitState.HALF_OPEN
        return self._state

    def call(self, func):
        if self.state is CircuitState.OPEN:
            raise CircuitOpenError(self.name)
        try:
            result = func()
        except TransientError:
            self._failures += 1
            if self._state is CircuitState.HALF_OPEN or self._failures >= self._threshold:
                self._state = CircuitState.OPEN
                self._opened_at = self._clock()
                logger.warning("Circuit '%s' -> OPEN", self.name)
            raise
        if self._state is not CircuitState.CLOSED:
            logger.info("Circuit '%s' -> CLOSED", self.name)
        self._state = CircuitState.CLOSED
        self._failures = 0
        return result

    def status(self) -> dict:
        return {"name": self.name, "state": self.state.value,
                "failures": self._failures, "threshold": self._threshold}


def retry_with_backoff(func, attempts=3, base_delay=0.5, factor=2.0, sleep=time.sleep):
    """Espera base_delay, base_delay*factor, ... entre intentos (0.5 s, 1 s, 2 s...)."""
    delay = base_delay
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except TransientError as error:
            if attempt == attempts:
                raise
            logger.warning("Attempt %s/%s failed (%s). Retrying in %.1fs",
                           attempt, attempts, error, delay)
            sleep(delay)
            delay *= factor


def default_transport(url, timeout):
    peticion = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(peticion, timeout=timeout) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except HTTPError as error:  # va primero: HTTPError es subclase de URLError
        if error.code == 429 or error.code >= 500:
            raise TransientError(f"HTTP {error.code}") from error
        raise PermanentError(f"HTTP {error.code}") from error
    except (TimeoutError, URLError, OSError) as error:
        raise TransientError(f"Network error: {error}") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise PermanentError("Invalid JSON received") from error


class ResilientJsonClient:
    """GET JSON: el retry va dentro y el circuit breaker por fuera."""

    def __init__(self, name, breaker, attempts=3, base_delay=0.5, timeout=10.0,
                 transport=default_transport, sleep=time.sleep):
        self.name, self.breaker = name, breaker
        self._attempts, self._base_delay, self._timeout = attempts, base_delay, timeout
        self._transport, self._sleep = transport, sleep

    def get_json(self, url):
        def con_reintentos():
            return retry_with_backoff(lambda: self._transport(url, self._timeout),
                                      self._attempts, self._base_delay, sleep=self._sleep)
        try:
            return self.breaker.call(con_reintentos)
        except CircuitOpenError as error:
            raise CircuitOpen(f"{self.name} is temporarily unavailable (circuit open).") from error
        except (TransientError, PermanentError) as error:
            raise UpstreamFailure(f"{self.name} failed: {error}") from error
