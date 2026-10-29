from pydantic import BaseModel, Field, field_validator


def _limpiar(valor):
    valor = valor.strip()
    if not valor:
        raise ValueError("This field cannot be empty.")
    return valor


class ProductoSchema(BaseModel):
    id: int = Field(description="Unique product identifier")
    nombre: str = Field(min_length=1, description="Product name")
    categoria: str = Field(min_length=1, description="Product category")
    precio: float = Field(gt=0, description="Price must be positive")
    stock: int = Field(ge=0, description="Stock cannot be negative")

    @field_validator("nombre", "categoria")
    @classmethod
    def validar_texto(cls, valor):
        return _limpiar(valor)


class ProductoActualizar(BaseModel):
    nombre: str = Field(min_length=1)
    categoria: str = Field(min_length=1)
    precio: float = Field(gt=0)
    stock: int = Field(ge=0)

    @field_validator("nombre", "categoria")
    @classmethod
    def validar_texto(cls, valor):
        return _limpiar(valor)


class AIRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    technique: str = "zero-shot"

    @field_validator("query")
    @classmethod
    def validar_consulta(cls, valor):
        valor = valor.strip()
        if not valor:
            raise ValueError("The query cannot be empty.")
        return valor

    @field_validator("technique")
    @classmethod
    def validar_tecnica(cls, valor):
        valor = valor.strip().lower()
        if valor not in {"zero-shot", "few-shot", "cot"}:
            raise ValueError("Use zero-shot, few-shot or cot.")
        return valor


class AIResponse(BaseModel):
    answer: str
    technique: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
