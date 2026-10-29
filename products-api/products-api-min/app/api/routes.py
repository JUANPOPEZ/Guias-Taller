from dataclasses import asdict

from fastapi import APIRouter, Query, Request

from app.api.schemas import AIRequest, AIResponse, ProductoActualizar, ProductoSchema
from app.domain.inventory import Producto

router = APIRouter()


def _c(request: Request):
    """Devuelve el contenedor con los servicios ya armados."""
    return request.app.state.container


# ---- Products (CRUD) ----
@router.get("/productos", response_model=list[ProductoSchema], tags=["Products"],
            summary="List all products")
def obtener_productos(request: Request):
    return [asdict(p) for p in _c(request).product_service.list_products()]


@router.get("/productos/{id_producto}", response_model=ProductoSchema, tags=["Products"],
            summary="Get a product by ID")
def obtener_producto(id_producto: int, request: Request):
    return asdict(_c(request).product_service.get_product(id_producto))


@router.post("/productos", response_model=ProductoSchema, status_code=201, tags=["Products"],
             summary="Create a product")
def crear_producto(producto: ProductoSchema, request: Request):
    return asdict(_c(request).product_service.create_product(Producto(**producto.model_dump())))


@router.put("/productos/{id_producto}", response_model=ProductoSchema, tags=["Products"],
            summary="Update a product")
def actualizar_producto(id_producto: int, datos: ProductoActualizar, request: Request):
    return asdict(_c(request).product_service.update_product(id_producto, **datos.model_dump()))


@router.delete("/productos/{id_producto}", response_model=ProductoSchema, tags=["Products"],
               summary="Delete a product")
def eliminar_producto(id_producto: int, request: Request):
    return asdict(_c(request).product_service.delete_product(id_producto))


# ---- Artificial Intelligence ----
@router.post("/api/v1/ai", response_model=AIResponse, tags=["Artificial Intelligence"],
             summary="Ask Gemini about the product inventory")
def consultar_ia(consulta: AIRequest, request: Request):
    return asdict(_c(request).assistant_service.ask(consulta.query, consulta.technique))


# ---- Open Data (Colombia) ----
@router.get("/api/v1/open-data/trm-statistics", tags=["Open Data (Colombia)"],
            summary="TRM descriptive statistics (datos.gov.co + DuckDB)")
def trm_statistics(request: Request, days: int = Query(30, ge=2, le=365)):
    return _c(request).open_data_service.trm_statistics(days)


@router.get("/api/v1/open-data/municipalities", tags=["Open Data (Colombia)"],
            summary="Municipalities per department (DANE codes + DuckDB)")
def municipalities(request: Request):
    return _c(request).open_data_service.municipalities_by_department()


@router.get("/api/v1/open-data/circuit-breakers", tags=["Open Data (Colombia)"],
            summary="State of each circuit breaker (CLOSED / OPEN / HALF_OPEN)")
def circuit_breakers(request: Request):
    return [b.status() for b in _c(request).breakers]
