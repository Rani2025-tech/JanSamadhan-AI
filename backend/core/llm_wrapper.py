import os
import time
import json
import re
from collections import OrderedDict
from typing import Generator, Optional, Dict, Any, List, Tuple
import httpx

class LLMUnavailable(Exception):
    """Raised when all configured LLM providers and keys are exhausted or rate-limited."""
    pass

# Endpoints
GROQ_API_BASE = "https://api.groq.com/openai/v1"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"

# Default models & timeout
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_TIMEOUT = 20.0

# Cooldown tracking: key -> timestamp until which it is on cooldown
_cooldowns: Dict[str, float] = {}

# Tracking last used provider
_last_provider: Optional[str] = None

# In-memory LRU cache
_CACHE_MAX_SIZE = 256
_cache: OrderedDict = OrderedDict()

def cache_clear():
    """Clear the in-memory response cache."""
    global _cache
    _cache.clear()

def last_provider() -> Optional[str]:
    """Return the name of the provider that successfully served the last call."""
    return _last_provider

def _get_env_keys(keys_var: str, single_var: str) -> List[str]:
    val = os.getenv(keys_var, "").strip()
    if val:
        keys = [k.strip() for k in val.split(",") if k.strip()]
        if keys:
            return keys
    single = os.getenv(single_var, "").strip()
    if single:
        return [single]
    return []

def _get_configured_providers() -> List[Tuple[str, str, str, str]]:
    """
    Returns ordered list of (provider_name, api_key, base_url, model_name).
    Groq keys first, followed by Gemini keys.
    """
    groq_keys = _get_env_keys("GROQ_API_KEYS", "GROQ_API_KEY")
    gemini_keys = _get_env_keys("GEMINI_API_KEYS", "GEMINI_API_KEY")

    groq_model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL
    gemini_model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL

    providers = []
    for k in groq_keys:
        providers.append(("groq", k, GROQ_API_BASE, groq_model))
    for k in gemini_keys:
        providers.append(("gemini", k, GEMINI_API_BASE, gemini_model))
    return providers

def _is_cooled_down(key: str) -> bool:
    expiry = _cooldowns.get(key, 0.0)
    return time.time() < expiry

def _set_cooldown(key: str, response: Optional[httpx.Response] = None):
    cooldown_seconds = 60.0
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                cooldown_seconds = float(retry_after)
            except ValueError:
                cooldown_seconds = 60.0
    _cooldowns[key] = time.time() + cooldown_seconds

def _get_timeout() -> float:
    try:
        return float(os.getenv("LLM_TIMEOUT", DEFAULT_TIMEOUT))
    except (ValueError, TypeError):
        return DEFAULT_TIMEOUT

def _build_messages(prompt: str, system: Optional[str] = None) -> List[Dict[str, str]]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages

def _clean_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()

def chat(prompt: str, system: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 800) -> str:
    global _last_provider

    cache_key = ("chat", system, prompt, temperature, max_tokens)
    if cache_key in _cache:
        _cache.move_to_end(cache_key)
        return _cache[cache_key]

    providers = _get_configured_providers()
    if not providers:
        raise LLMUnavailable("No LLM API keys configured.")

    timeout = _get_timeout()
    messages = _build_messages(prompt, system)
    payload = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    tried_any = False
    for provider, key, base_url, model in providers:
        if _is_cooled_down(key):
            continue

        tried_any = True
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        body = {**payload, "model": model}

        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.post(url, headers=headers, json=body)

            if res.status_code == 429 or res.status_code >= 500:
                _set_cooldown(key, res)
                continue
            elif res.status_code != 200:
                res.raise_for_status()

            data = res.json()
            content = data["choices"][0]["message"]["content"]
            _last_provider = provider

            # Cache response
            _cache[cache_key] = content
            if len(_cache) > _CACHE_MAX_SIZE:
                _cache.popitem(last=False)

            return content

        except (httpx.TimeoutException, httpx.ConnectError):
            _set_cooldown(key)
            continue
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 or e.response.status_code >= 500:
                _set_cooldown(key, e.response)
                continue
            # Non-fallback 4xx errors
            raise

    raise LLMUnavailable("All configured LLM providers and keys are currently unavailable.")

def chat_json(prompt: str, system: Optional[str] = None) -> dict:
    global _last_provider

    cache_key = ("chat_json", system, prompt)
    if cache_key in _cache:
        _cache.move_to_end(cache_key)
        return _cache[cache_key]

    providers = _get_configured_providers()
    if not providers:
        raise LLMUnavailable("No LLM API keys configured.")

    timeout = _get_timeout()
    messages = _build_messages(prompt, system)
    payload = {
        "messages": messages,
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }

    last_error: Optional[Exception] = None

    for attempt in range(2):
        for provider, key, base_url, model in providers:
            if _is_cooled_down(key):
                continue

            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            body = {**payload, "model": model}

            try:
                with httpx.Client(timeout=timeout) as client:
                    res = client.post(url, headers=headers, json=body)

                if res.status_code == 429 or res.status_code >= 500:
                    _set_cooldown(key, res)
                    continue
                elif res.status_code != 200:
                    res.raise_for_status()

                data = res.json()
                raw_text = data["choices"][0]["message"]["content"]
                cleaned = _clean_json_fences(raw_text)

                try:
                    result = json.loads(cleaned)
                    _last_provider = provider
                    _cache[cache_key] = result
                    if len(_cache) > _CACHE_MAX_SIZE:
                        _cache.popitem(last=False)
                    return result
                except (json.JSONDecodeError, ValueError) as json_err:
                    last_error = json_err
                    break  # retry attempt outer loop

            except (httpx.TimeoutException, httpx.ConnectError):
                _set_cooldown(key)
                continue
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 or e.response.status_code >= 500:
                    _set_cooldown(key, e.response)
                    continue
                raise

    if last_error:
        raise ValueError(f"Failed to parse LLM JSON output after retry: {last_error}")
    raise LLMUnavailable("All configured LLM providers and keys are currently unavailable.")

def chat_stream(prompt: str, system: Optional[str] = None) -> Generator[str, None, None]:
    global _last_provider

    providers = _get_configured_providers()
    if not providers:
        raise LLMUnavailable("No LLM API keys configured.")

    timeout = _get_timeout()
    messages = _build_messages(prompt, system)
    payload = {
        "messages": messages,
        "temperature": 0.2,
        "stream": True
    }

    yielded_any = False

    for provider, key, base_url, model in providers:
        if _is_cooled_down(key):
            continue

        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        body = {**payload, "model": model}

        try:
            with httpx.Client(timeout=timeout) as client:
                with client.stream("POST", url, headers=headers, json=body) as res:
                    if res.status_code == 429 or res.status_code >= 500:
                        _set_cooldown(key, res)
                        continue
                    elif res.status_code != 200:
                        res.read()
                        res.raise_for_status()

                    _last_provider = provider

                    for line in res.iter_lines():
                        if not line:
                            continue
                        line_str = line.strip()
                        if line_str.startswith("data:"):
                            chunk_data = line_str[5:].strip()
                            if chunk_data == "[DONE]":
                                break
                            try:
                                parsed = json.loads(chunk_data)
                                delta = parsed.get("choices", [{}])[0].get("delta", {})
                                text = delta.get("content", "")
                                if text:
                                    yielded_any = True
                                    yield text
                            except Exception:
                                pass
            return

        except (httpx.TimeoutException, httpx.ConnectError):
            if yielded_any:
                raise
            _set_cooldown(key)
            continue
        except httpx.HTTPStatusError as e:
            if yielded_any:
                raise
            if e.response.status_code == 429 or e.response.status_code >= 500:
                _set_cooldown(key, e.response)
                continue
            raise
        except Exception:
            if yielded_any:
                raise
            continue

    if not yielded_any:
        raise LLMUnavailable("All configured LLM providers and keys are currently unavailable.")

# Backward-compatibility adapter for LangChain-style invocations
class _CompatResult:
    def __init__(self, content: str):
        self.content = content

class _CompatChunk:
    def __init__(self, content: str):
        self.content = content

class LLMCompat:
    def invoke(self, prompt: str) -> _CompatResult:
        return _CompatResult(chat(prompt))

    def stream(self, prompt: str) -> Generator[_CompatChunk, None, None]:
        for token in chat_stream(prompt):
            yield _CompatChunk(token)

