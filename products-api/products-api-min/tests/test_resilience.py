import unittest
from unittest.mock import Mock

from app.domain.errors import CircuitOpen, UpstreamFailure
from app.infrastructure.resilience import (
    CircuitBreaker, CircuitOpenError, CircuitState, ResilientJsonClient,
    TransientError, retry_with_backoff,
)


def fallar():
    raise TransientError("boom")


class TestCircuitBreaker(unittest.TestCase):
    def test_pasa_por_los_tres_estados(self):
        reloj = [0.0]
        breaker = CircuitBreaker("test", 3, 30, clock=lambda: reloj[0])
        self.assertEqual(breaker.state, CircuitState.CLOSED)

        for _ in range(3):
            with self.assertRaises(TransientError):
                breaker.call(fallar)
        self.assertEqual(breaker.state, CircuitState.OPEN)

        with self.assertRaises(CircuitOpenError):       # abierto: ni llama a la función
            breaker.call(Mock())

        reloj[0] = 31
        self.assertEqual(breaker.state, CircuitState.HALF_OPEN)

        self.assertEqual(breaker.call(lambda: "ok"), "ok")
        self.assertEqual(breaker.state, CircuitState.CLOSED)


class TestRetry(unittest.TestCase):
    def test_backoff_exponencial(self):
        pausas = []
        funcion = Mock(side_effect=[TransientError("1"), TransientError("2"), "listo"])
        self.assertEqual(retry_with_backoff(funcion, 3, 0.5, sleep=pausas.append), "listo")
        self.assertEqual(pausas, [0.5, 1.0])


class TestClient(unittest.TestCase):
    def test_tres_peticiones_fallidas_abren_el_circuito(self):
        transport = Mock(side_effect=TransientError("down"))
        client = ResilientJsonClient("api", CircuitBreaker("api", 3, 30), 3, 0.01,
                                     transport=transport, sleep=lambda s: None)
        for _ in range(3):
            with self.assertRaises(UpstreamFailure):
                client.get_json("http://x")
        with self.assertRaises(CircuitOpen):
            client.get_json("http://x")
        self.assertEqual(transport.call_count, 9)   # el 4º ni salió a la red


if __name__ == "__main__":
    unittest.main()
