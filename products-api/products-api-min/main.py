import logging
import sys

from app.api.app import create_app
from app.composition import build_container

logging.basicConfig(level=logging.INFO)

app = create_app(build_container())

# Tu comando de siempre para el pipeline:  python main.py --test
if __name__ == "__main__" and "--test" in sys.argv:
    import unittest
    resultado = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.discover("tests"))
    sys.exit(0 if resultado.wasSuccessful() else 1)
