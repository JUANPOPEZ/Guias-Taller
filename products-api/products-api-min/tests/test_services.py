"""Testabilidad de la DI: los servicios se prueban con mocks (el 'Mockito' de Python)."""
import unittest
from unittest.mock import Mock

from app.application.services import AssistantService, ProductService
from app.domain.errors import DuplicateProduct
from app.domain.inventory import LLMAnswer, Producto


class TestServices(unittest.TestCase):
    def test_id_duplicado_no_guarda(self):
        repo = Mock()
        repo.get.return_value = Producto(1, "Teclado", "Perifericos", 85000, 10)
        with self.assertRaises(DuplicateProduct):
            ProductService(repo).create_product(Producto(1, "Otro", "X", 1, 1))
        repo.save.assert_not_called()

    def test_few_shot_incluye_ejemplo_e_inventario(self):
        repo, llm = Mock(), Mock(model_name="fake")
        repo.list_all.return_value = [Producto(1, "Teclado", "Perifericos", 85000, 10)]
        llm.generate.return_value = LLMAnswer("Hay 10", 20, 3)

        resultado = AssistantService(repo, llm).ask("¿Hay teclados?", "few-shot")

        prompt = llm.generate.call_args.args[0]
        self.assertIn("Example:", prompt)
        self.assertIn("Teclado", prompt)
        self.assertEqual((resultado.answer, resultado.model), ("Hay 10", "fake"))


if __name__ == "__main__":
    unittest.main()
