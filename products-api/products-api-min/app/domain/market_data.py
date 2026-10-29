"""Bounded context 2: Market Data (datos abiertos colombianos)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ExchangeRate:
    fecha: date
    valor: float  # pesos por dólar (TRM)


@dataclass(frozen=True)
class Municipality:
    codigo_dane: str
    municipio: str
    departamento: str


class ExchangeRateProvider(ABC):
    @abstractmethod
    def get_history(self, days: int) -> list[ExchangeRate]: ...


class MunicipalityProvider(ABC):
    @abstractmethod
    def list_municipalities(self) -> list[Municipality]: ...


class AnalyticsEngine(ABC):
    """Puerto: motor de análisis SQL (lo implementa DuckDB)."""

    @abstractmethod
    def trm_statistics(self, rates: list[ExchangeRate]) -> dict: ...

    @abstractmethod
    def municipalities_by_department(self, municipalities: list[Municipality]) -> list[dict]: ...
