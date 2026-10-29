"""Casos de uso. Cada servicio recibe sus dependencias por el constructor (DI)."""
import json
import logging
from dataclasses import asdict, dataclass

from app.domain.errors import DuplicateProduct, ProductNotFound
from app.domain.inventory import LLMGateway, ProductRepository, Producto
from app.domain.market_data import AnalyticsEngine, ExchangeRateProvider, MunicipalityProvider

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, repository: ProductRepository):
        self._repository = repository

    def list_products(self):
        return self._repository.list_all()

    def get_product(self, product_id: int) -> Producto:
        producto = self._repository.get(product_id)
        if producto is None:
            raise ProductNotFound("Product not found")
        return producto

    def create_product(self, producto: Producto) -> Producto:
        if self._repository.get(producto.id) is not None:
            raise DuplicateProduct("Product ID already exists")
        self._repository.save(producto)
        logger.info("Product created: %s", producto.id)
        return producto

    def update_product(self, product_id, nombre, categoria, precio, stock) -> Producto:
        producto = self.get_product(product_id)
        producto.nombre, producto.categoria = nombre, categoria
        producto.precio, producto.stock = precio, stock
        self._repository.save(producto)
        logger.info("Product updated: %s", product_id)
        return producto

    def delete_product(self, product_id: int) -> Producto:
        producto = self.get_product(product_id)
        self._repository.delete(product_id)
        logger.info("Product deleted: %s", product_id)
        return producto


@dataclass
class AssistantResult:
    answer: str
    technique: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class AssistantService:
    def __init__(self, repository: ProductRepository, llm: LLMGateway):
        self._repository = repository
        self._llm = llm

    def build_prompt(self, query: str, technique: str) -> str:
        instrucciones = (
            "You are a product inventory assistant. Answer in Spanish. "
            "Use only the supplied inventory and do not invent information."
        )
        if technique == "few-shot":
            instrucciones += (
                "\nExample: Question: Is the keyboard available? "
                "Answer: Check the recorded stock before responding."
            )
        elif technique == "cot":
            instrucciones += (
                "\nAnalyze the available information carefully and provide "
                "a concise answer with a brief justification. Do not reveal "
                "private internal reasoning."
            )
        inventario = json.dumps([asdict(p) for p in self._repository.list_all()],
                                ensure_ascii=False)
        return f"{instrucciones}\nInventory: {inventario}\nQuestion: {query}"

    def ask(self, query: str, technique: str) -> AssistantResult:
        respuesta = self._llm.generate(self.build_prompt(query, technique))
        logger.info("AI request completed: %s", technique)
        return AssistantResult(respuesta.answer, technique, self._llm.model_name,
                               respuesta.input_tokens, respuesta.output_tokens)


class OpenDataService:
    def __init__(self, exchange_rates: ExchangeRateProvider,
                 municipalities: MunicipalityProvider, engine: AnalyticsEngine):
        self._exchange_rates = exchange_rates
        self._municipalities = municipalities
        self._engine = engine

    def trm_statistics(self, days: int) -> dict:
        return self._engine.trm_statistics(self._exchange_rates.get_history(days))

    def municipalities_by_department(self) -> list[dict]:
        return self._engine.municipalities_by_department(
            self._municipalities.list_municipalities())
