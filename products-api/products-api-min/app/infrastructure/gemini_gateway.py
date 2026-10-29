import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.domain.errors import RateLimited, ServiceNotConfigured, UpstreamFailure, UpstreamTimeout
from app.domain.inventory import LLMAnswer, LLMGateway

logger = logging.getLogger(__name__)


class GeminiLLMGateway(LLMGateway):
    """Tu consultar_gemini de la Guía 5, convertida en clase."""

    def __init__(self, api_key, model, timeout=20):
        self._api_key = api_key
        self.model_name = model
        self._timeout = timeout

    def generate(self, prompt):
        if not self._api_key:
            raise ServiceNotConfigured("Gemini API key is not configured.")
        url = ("https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model_name}:generateContent?{urlencode({'key': self._api_key})}")
        cuerpo = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 500},
        }).encode("utf-8")
        peticion = Request(url, data=cuerpo, headers={"Content-Type": "application/json"},
                           method="POST")
        try:
            with urlopen(peticion, timeout=self._timeout) as respuesta:
                datos = json.loads(respuesta.read().decode("utf-8"))
        except HTTPError as error:
            if error.code == 429:
                raise RateLimited("Gemini rate limit exceeded.") from error
            logger.error("Gemini HTTP error: %s", error.code)
            raise UpstreamFailure("Gemini provider error.") from error
        except (TimeoutError, URLError) as error:
            raise UpstreamTimeout("Gemini request timed out or failed.") from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise UpstreamFailure("Invalid response from Gemini.") from error
        try:
            texto = datos["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as error:
            raise UpstreamFailure("Gemini returned no usable answer.") from error
        uso = datos.get("usageMetadata", {})
        return LLMAnswer(texto, uso.get("promptTokenCount"), uso.get("candidatesTokenCount"))
