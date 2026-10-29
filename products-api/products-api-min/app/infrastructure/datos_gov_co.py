"""Las dos APIs públicas colombianas (Socrata de datos.gov.co)."""
from datetime import date
from urllib.parse import urlencode

from app.domain.errors import UpstreamFailure
from app.domain.market_data import (
    ExchangeRate, ExchangeRateProvider, Municipality, MunicipalityProvider,
)


class DatosGovCoExchangeRateProvider(ExchangeRateProvider):
    """API 1: TRM (Superfinanciera)."""

    def __init__(self, client, base_url, resource):
        self._client = client
        self._url = f"{base_url}/resource/{resource}.json"

    def get_history(self, days):
        query = urlencode({"$order": "vigenciadesde DESC", "$limit": days})
        datos = self._client.get_json(f"{self._url}?{query}")
        try:
            tasas = [ExchangeRate(date.fromisoformat(f["vigenciadesde"][:10]), float(f["valor"]))
                     for f in datos]
        except (KeyError, TypeError, ValueError) as error:
            raise UpstreamFailure("TRM API returned an unexpected format.") from error
        if not tasas:
            raise UpstreamFailure("TRM API returned no data.")
        return sorted(tasas, key=lambda t: t.fecha)


class DaneMunicipalityProvider(MunicipalityProvider):
    """API 2: municipios con código DANE (DIVIPOLA)."""

    def __init__(self, client, base_url, resource):
        self._client = client
        self._url = f"{base_url}/resource/{resource}.json"

    def list_municipalities(self):
        datos = self._client.get_json(f"{self._url}?{urlencode({'$limit': 2000})}")
        try:
            municipios = [Municipality(str(f["c_digo_dane_del_municipio"]),
                                       f["municipio"], f["departamento"]) for f in datos]
        except (KeyError, TypeError) as error:
            raise UpstreamFailure("DANE API returned an unexpected format.") from error
        if not municipios:
            raise UpstreamFailure("DANE API returned no data.")
        return municipios
