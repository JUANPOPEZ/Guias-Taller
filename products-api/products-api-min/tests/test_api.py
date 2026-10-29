"""Tus 3 pruebas originales, ahora sobre la arquitectura hexagonal."""
import unittest
from datetime import date
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.api.app import create_app
from app.application.services import AssistantService, OpenDataService, ProductService
from app.composition import Container
from app.domain.errors import CircuitOpen
from app.domain.market_data import ExchangeRate
from app.infrastructure.duckdb_engine import DuckDBAnalyticsEngine
from app.infrastructure.in_memory_product_repository import InMemoryProductRepository


def make_client(exchange_rates=None):
    repo = InMemoryProductRepository()
    rates = exchange_rates or Mock()
    if exchange_rates is None:
        rates.get_history.return_value = [ExchangeRate(date(2026, 10, 7), 3216.01),
                                          ExchangeRate(date(2026, 10, 8), 3238.88)]
    container = Container(
        product_service=ProductService(repo),
        assistant_service=AssistantService(repo, Mock()),
        open_data_service=OpenDataService(rates, Mock(), DuckDBAnalyticsEngine()),
    )
    return TestClient(create_app(container))


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = make_client()

    def test_crear_y_consultar(self):
        datos = {"id": 1, "nombre": "Teclado", "categoria": "Perifericos",
                 "precio": 85000, "stock": 10}
        self.assertEqual(self.client.post("/productos", json=datos).status_code, 201)
        respuesta = self.client.get("/productos/1")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["nombre"], "Teclado")

    def test_id_duplicado(self):
        datos = {"id": 2, "nombre": "Mouse", "categoria": "Perifericos",
                 "precio": 45000, "stock": 5}
        self.client.post("/productos", json=datos)
        self.assertEqual(self.client.post("/productos", json=datos).status_code, 409)

    def test_producto_inexistente(self):
        self.assertEqual(self.client.get("/productos/999").status_code, 404)

    def test_estadisticas_trm_por_el_endpoint(self):
        r = self.client.get("/api/v1/open-data/trm-statistics?days=2")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["observations"], 2)

    def test_circuito_abierto_responde_503(self):
        rates = Mock()
        rates.get_history.side_effect = CircuitOpen("TRM unavailable (circuit open).")
        r = make_client(rates).get("/api/v1/open-data/trm-statistics")
        self.assertEqual(r.status_code, 503)


if __name__ == "__main__":
    unittest.main()
