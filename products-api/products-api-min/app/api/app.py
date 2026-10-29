from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.api.routes import router
from app.domain.errors import (
    CircuitOpen, DomainError, DuplicateProduct, ProductNotFound, RateLimited,
    ServiceNotConfigured, UpstreamFailure, UpstreamTimeout,
)

# Traducción de errores de dominio a códigos HTTP (esto vive en la capa api).
STATUS_BY_ERROR = {
    ProductNotFound: 404, DuplicateProduct: 409, ServiceNotConfigured: 503,
    CircuitOpen: 503, RateLimited: 429, UpstreamTimeout: 504, UpstreamFailure: 502,
}


def create_app(container) -> FastAPI:
    app = FastAPI(
        title="Products API",
        description="REST API for product management, AI and Colombian open data.",
        version="2.0.0",
        openapi_tags=[
            {"name": "Products", "description": "Product CRUD operations."},
            {"name": "Artificial Intelligence", "description": "Gemini integration."},
            {"name": "Open Data (Colombia)", "description": "datos.gov.co / DANE, DuckDB and circuit breakers."},
        ],
    )
    app.state.container = container

    @app.exception_handler(DomainError)
    async def manejar_error(request: Request, error: DomainError):
        return JSONResponse(status_code=STATUS_BY_ERROR.get(type(error), 400),
                            content={"detail": str(error)})

    app.include_router(router)

    @app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
    def dashboard():
        return (Path(__file__).parent / "static" / "dashboard.html").read_text(encoding="utf-8")

    return app
