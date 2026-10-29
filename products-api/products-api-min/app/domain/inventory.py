"""Bounded context 1: Inventory (productos y asistente de IA)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Producto:
    id: int
    nombre: str
    categoria: str
    precio: float
    stock: int


class ProductRepository(ABC):
    """Puerto: cómo se guardan y buscan los productos."""

    @abstractmethod
    def list_all(self) -> list[Producto]: ...

    @abstractmethod
    def get(self, product_id: int) -> Producto | None: ...

    @abstractmethod
    def save(self, producto: Producto) -> None: ...

    @abstractmethod
    def delete(self, product_id: int) -> None: ...


@dataclass
class LLMAnswer:
    answer: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMGateway(ABC):
    """Puerto: cómo se le pregunta algo a un modelo de lenguaje."""
    model_name: str

    @abstractmethod
    def generate(self, prompt: str) -> LLMAnswer: ...
