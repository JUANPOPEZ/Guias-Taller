import unittest
from datetime import date
from unittest.mock import Mock

from app.domain.market_data import ExchangeRate, Municipality
from app.infrastructure.datos_gov_co import DatosGovCoExchangeRateProvider
from app.infrastructure.duckdb_engine import DuckDBAnalyticsEngine


class TestDuckDB(unittest.TestCase):
    def test_estadisticas_descriptivas_trm(self):
        tasas = [ExchangeRate(date(2026, 10, 5), 3273.49), ExchangeRate(date(2026, 10, 6), 3209.78),
                 ExchangeRate(date(2026, 10, 7), 3216.01), ExchangeRate(date(2026, 10, 8), 3238.88)]
        s = DuckDBAnalyticsEngine().trm_statistics(tasas)
        self.assertEqual(s["observations"], 4)
        self.assertEqual((s["minimum"], s["maximum"], s["mean"]), (3209.78, 3273.49, 3234.54))

    def test_municipios_por_departamento(self):
        municipios = [Municipality("05001", "Medellín", "Antioquia"),
                      Municipality("05002", "Abejorral", "Antioquia"),
                      Municipality("08001", "Barranquilla", "Atlántico")]
        r = DuckDBAnalyticsEngine().municipalities_by_department(municipios)
        self.assertEqual(r[0], {"department": "Antioquia", "municipalities": 2})


class TestAdaptador(unittest.TestCase):
    def test_trm_parsea_el_json_de_socrata(self):
        client = Mock()
        client.get_json.return_value = [
            {"valor": "3238.88", "vigenciadesde": "2026-10-08T00:00:00.000"},
            {"valor": "3216.01", "vigenciadesde": "2026-10-07T00:00:00.000"}]
        tasas = DatosGovCoExchangeRateProvider(client, "https://www.datos.gov.co", "32sa-8pi3").get_history(2)
        self.assertEqual([t.valor for t in tasas], [3216.01, 3238.88])


if __name__ == "__main__":
    unittest.main()
