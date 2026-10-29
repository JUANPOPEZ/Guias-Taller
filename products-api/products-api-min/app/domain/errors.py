class DomainError(Exception):
    """Base de los errores del dominio."""


class ProductNotFound(DomainError):
    pass


class DuplicateProduct(DomainError):
    pass


# Errores al hablar con servicios externos (Gemini, datos.gov.co)
class ServiceNotConfigured(DomainError):
    pass


class RateLimited(DomainError):
    pass


class UpstreamTimeout(DomainError):
    pass


class UpstreamFailure(DomainError):
    pass


class CircuitOpen(DomainError):
    pass
