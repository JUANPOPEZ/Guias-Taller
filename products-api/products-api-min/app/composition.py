"""Aquí (y solo aquí) se crean los objetos reales y se conectan entre sí."""
import os
from dataclasses import dataclass, field

from app.application.services import AssistantService, OpenDataService, ProductService
from app.infrastructure.datos_gov_co import (
    DaneMunicipalityProvider, DatosGovCoExchangeRateProvider,
)
from app.infrastructure.duckdb_engine import DuckDBAnalyticsEngine
from app.infrastructure.gemini_gateway import GeminiLLMGateway
from app.infrastructure.in_memory_product_repository import InMemoryProductRepository
from app.infrastructure.resilience import CircuitBreaker, ResilientJsonClient


@dataclass
class Container:
    product_service: ProductService
    assistant_service: AssistantService
    open_data_service: OpenDataService
    breakers: list = field(default_factory=list)


def build_container() -> Container:
    base_url = os.getenv("DATOS_BASE_URL", "https://www.datos.gov.co")
    trm_resource = os.getenv("TRM_RESOURCE", "32sa-8pi3")
    divipola_resource = os.getenv("DIVIPOLA_RESOURCE", "xdk5-pm3f")
    recovery = float(os.getenv("CB_RECOVERY_SECONDS", "30"))

    def cliente(nombre):
        return ResilientJsonClient(nombre, CircuitBreaker(nombre, 3, recovery))

    trm_client = cliente("datos.gov.co TRM")
    dane_client = cliente("DANE DIVIPOLA")

    repository = InMemoryProductRepository()
    llm = GeminiLLMGateway(os.getenv("GEMINI_API_KEY"),
                           os.getenv("GEMINI_MODEL", "gemini-3.6-flash"))
    return Container(
        product_service=ProductService(repository),
        assistant_service=AssistantService(repository, llm),
        open_data_service=OpenDataService(
            DatosGovCoExchangeRateProvider(trm_client, base_url, trm_resource),
            DaneMunicipalityProvider(dane_client, base_url, divipola_resource),
            DuckDBAnalyticsEngine()),
        breakers=[trm_client.breaker, dane_client.breaker],
    )
