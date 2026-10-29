from app.domain.inventory import ProductRepository, Producto


class InMemoryProductRepository(ProductRepository):
    """Reemplaza la lista global `productos` de tu main.py."""

    def __init__(self):
        self._items: dict[int, Producto] = {}

    def list_all(self):
        return list(self._items.values())

    def get(self, product_id):
        return self._items.get(product_id)

    def save(self, producto):
        self._items[producto.id] = producto

    def delete(self, product_id):
        self._items.pop(product_id, None)
