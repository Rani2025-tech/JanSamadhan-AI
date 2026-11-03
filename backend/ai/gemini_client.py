import json
import logging
from typing import Optional, Dict, Any, List
from app.config import settings
from .security import mask_phone_numbers

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.embedding_model = settings.GEMINI_EMBEDDING_MODEL
        self._client = None
        self._network_offline = False
        
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info("Initialized Google GenAI client successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai client: {e}")

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and self._client and not self._network_offline)

    def generate_content(self, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        if not self.is_available:
            return None
        
        # PII Masking: mask phone numbers before any LLM call
        sanitized_prompt = mask_phone_numbers(prompt)
        
        try:
            from google.genai import types
            config = types.GenerateContentConfig(
                temperature=0.1,
                top_p=0.95,
            )
            if system_instruction:
                config.system_instruction = system_instruction
                
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=sanitized_prompt,
                config=config
            )
            return response.text
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}")
            if "getaddrinfo failed" in str(e) or "ConnectError" in str(e):
                self._network_offline = True
            return None

    def embed_content(self, text: str) -> Optional[List[float]]:
        """Generates multilingual text embedding vector using Gemini."""
        if not self.is_available:
            return None
        
        sanitized_text = mask_phone_numbers(text)
        try:
            res = self._client.models.embed_content(
                model=self.embedding_model,
                contents=sanitized_text
            )
            if hasattr(res, "embedding") and hasattr(res.embedding, "values"):
                return list(res.embedding.values)
            elif hasattr(res, "embeddings") and len(res.embeddings) > 0:
                return list(res.embeddings[0].values)
            return None
        except Exception as e:
            logger.warning(f"Gemini embedding call failed: {e}")
            if "getaddrinfo failed" in str(e) or "ConnectError" in str(e):
                self._network_offline = True
            return None

gemini_client = GeminiClient()

def embed_content(text: str) -> Optional[List[float]]:
    return gemini_client.embed_content(text)
