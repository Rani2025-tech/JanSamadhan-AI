import os
import sys
import json
from unittest.mock import MagicMock, patch
import httpx
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.llm_wrapper import (
    chat,
    chat_json,
    chat_stream,
    last_provider,
    cache_clear,
    LLMUnavailable,
    _cooldowns
)

def _mock_response(status_code: int, json_data: dict = None, text: str = ""):
    req = httpx.Request("POST", "https://mock.api/chat/completions")
    content = json.dumps(json_data).encode("utf-8") if json_data else text.encode("utf-8")
    headers = {"Content-Type": "application/json"}
    return httpx.Response(status_code=status_code, content=content, headers=headers, request=req)

def run_all_tests():
    print("Running LLM Wrapper Tests...")

    # (a) Groq 429 falls back to Gemini
    cache_clear()
    _cooldowns.clear()
    with patch.dict(os.environ, {"GROQ_API_KEY": "g_key", "GEMINI_API_KEY": "gem_key", "GROQ_API_KEYS": "", "GEMINI_API_KEYS": ""}):
        calls = []
        def mock_post_a(self, url, **kwargs):
            calls.append(url)
            if "groq.com" in url:
                return _mock_response(429, {"error": "Rate limit exceeded"})
            return _mock_response(200, {"choices": [{"message": {"content": "Hello from Gemini"}}]})

        with patch.object(httpx.Client, "post", mock_post_a):
            res = chat("Hello")
            assert res == "Hello from Gemini"
            assert last_provider() == "gemini"
            assert len(calls) == 2
    print("Test (a) passed: Groq 429 falls back to Gemini.")

    # (b) Second Groq key is used when the first is rate-limited
    cache_clear()
    _cooldowns.clear()
    with patch.dict(os.environ, {"GROQ_API_KEYS": "g_key1,g_key2", "GEMINI_API_KEY": ""}):
        auth_headers = []
        def mock_post_b(self, url, **kwargs):
            auth = kwargs.get("headers", {}).get("Authorization", "")
            auth_headers.append(auth)
            if "g_key1" in auth:
                return _mock_response(429, {"error": "Rate limited key 1"})
            return _mock_response(200, {"choices": [{"message": {"content": "Success from key 2"}}]})

        with patch.object(httpx.Client, "post", mock_post_b):
            res = chat("Hi")
            assert res == "Success from key 2"
            assert last_provider() == "groq"
            assert "Bearer g_key1" in auth_headers[0]
            assert "Bearer g_key2" in auth_headers[1]
    print("Test (b) passed: Second Groq key used when first is 429.")

    # (c) A 400 error does not fall back
    cache_clear()
    _cooldowns.clear()
    with patch.dict(os.environ, {"GROQ_API_KEY": "g_key", "GEMINI_API_KEY": "gem_key"}):
        calls = []
        def mock_post_c(self, url, **kwargs):
            calls.append(url)
            return _mock_response(400, {"error": "Invalid request parameter"})

        with patch.object(httpx.Client, "post", mock_post_c):
            got_err = False
            try:
                chat("Test 400")
            except httpx.HTTPStatusError as e:
                got_err = True
                assert e.response.status_code == 400
            assert got_err, "Expected HTTPStatusError on 400"
            assert len(calls) == 1, "Should not attempt fallback on 400"
    print("Test (c) passed: 400 Bad Request does not trigger fallback.")

    # (d) All keys exhausted raises LLMUnavailable
    cache_clear()
    _cooldowns.clear()
    with patch.dict(os.environ, {"GROQ_API_KEY": "g_key", "GEMINI_API_KEY": "gem_key"}):
        def mock_post_d(self, url, **kwargs):
            return _mock_response(503, {"error": "Service Unavailable"})

        with patch.object(httpx.Client, "post", mock_post_d):
            got_exc = False
            try:
                chat("Hello")
            except LLMUnavailable:
                got_exc = True
            assert got_exc, "Expected LLMUnavailable when all keys fail"
    print("Test (d) passed: All keys exhausted raises LLMUnavailable.")

    # (e) Cached call makes no second request
    cache_clear()
    _cooldowns.clear()
    with patch.dict(os.environ, {"GROQ_API_KEY": "g_key"}):
        call_count = [0]
        def mock_post_e(self, url, **kwargs):
            call_count[0] += 1
            return _mock_response(200, {"choices": [{"message": {"content": "Cached output"}}]})

        with patch.object(httpx.Client, "post", mock_post_e):
            r1 = chat("Cache test", temperature=0.5)
            r2 = chat("Cache test", temperature=0.5)
            assert r1 == r2 == "Cached output"
            assert call_count[0] == 1, f"Expected 1 HTTP call, got {call_count[0]}"
    print("Test (e) passed: Cached call makes no second request.")

    # (f) chat_json strips code fences
    cache_clear()
    _cooldowns.clear()
    with patch.dict(os.environ, {"GROQ_API_KEY": "g_key"}):
        fenced_json = "```json\n{\n  \"status\": \"success\",\n  \"code\": 200\n}\n```"
        def mock_post_f(self, url, **kwargs):
            return _mock_response(200, {"choices": [{"message": {"content": fenced_json}}]})

        with patch.object(httpx.Client, "post", mock_post_f):
            data = chat_json("Get json")
            assert isinstance(data, dict)
            assert data["status"] == "success"
            assert data["code"] == 200
    print("Test (f) passed: chat_json strips markdown code fences.")

    # (g) Stream fallback happens only before the first chunk
    cache_clear()
    _cooldowns.clear()
    # Case g1: fallback before first chunk
    with patch.dict(os.environ, {"GROQ_API_KEY": "g_key", "GEMINI_API_KEY": "gem_key"}):
        stream_calls = []

        class MockStreamContext:
            def __init__(self, url):
                self.url = url
            def __enter__(self):
                stream_calls.append(self.url)
                if "groq.com" in self.url:
                    return _mock_response(429, {"error": "Rate limit on stream"})
                # Gemini stream returns SSE lines
                sse_data = "data: {\"choices\": [{\"delta\": {\"content\": \"Chunk 1 \"}}]}\n\ndata: {\"choices\": [{\"delta\": {\"content\": \"Chunk 2\"}}]}\n\ndata: [DONE]\n\n"
                return _mock_response(200, text=sse_data)
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_stream_g1(self, method, url, **kwargs):
            return MockStreamContext(url)

        with patch.object(httpx.Client, "stream", mock_stream_g1):
            chunks = list(chat_stream("Stream test"))
            assert "".join(chunks) == "Chunk 1 Chunk 2"
            assert len(stream_calls) == 2
            assert last_provider() == "gemini"

    # Case g2: error during stream after first chunk does NOT fall back
    cache_clear()
    _cooldowns.clear()
    with patch.dict(os.environ, {"GROQ_API_KEY": "g_key", "GEMINI_API_KEY": "gem_key"}):
        class FaultyStreamResponse:
            def __init__(self):
                self.status_code = 200
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
            def iter_lines(self):
                yield "data: {\"choices\": [{\"delta\": {\"content\": \"Started\"}}]}"
                raise httpx.ReadTimeout("Connection dropped mid-stream")

        def mock_stream_g2(self, method, url, **kwargs):
            return FaultyStreamResponse()

        with patch.object(httpx.Client, "stream", mock_stream_g2):
            gen = chat_stream("Stream fail mid-way")
            first = next(gen)
            assert first == "Started"
            error_propagated = False
            try:
                next(gen)
            except httpx.ReadTimeout:
                error_propagated = True
            assert error_propagated, "Mid-stream error should propagate and not fallback"

    print("Test (g) passed: Stream fallback happens only before first chunk.")

    print("\nALL LLM WRAPPER TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all_tests()

