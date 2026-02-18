import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from aioresponses import aioresponses
from api.generators.prompt.ollama_expander import OllamaPromptExpander


class TestOllamaPromptExpander:
    def _make_expander(self):
        expander = OllamaPromptExpander()
        expander.base_url = "http://test-ollama:11434"
        expander.model = "gemma3:12b"
        return expander

    async def test_successful_expansion(self):
        expander = self._make_expander()

        with aioresponses() as m:
            m.post(
                "http://test-ollama:11434/api/generate",
                payload={"response": "A cinematic shot of a cat walking slowly..."},
            )

            result = await expander.expand_prompt("cat on street")

        assert result == "A cinematic shot of a cat walking slowly..."

    async def test_strips_wrapping_quotes(self):
        expander = self._make_expander()

        with aioresponses() as m:
            m.post(
                "http://test-ollama:11434/api/generate",
                payload={"response": '"A cinematic shot of a cat walking slowly..."'},
            )

            result = await expander.expand_prompt("cat on street")

        assert not result.startswith('"')
        assert not result.endswith('"')
        assert result == "A cinematic shot of a cat walking slowly..."

    async def test_does_not_strip_unmatched_quotes(self):
        expander = self._make_expander()

        with aioresponses() as m:
            m.post(
                "http://test-ollama:11434/api/generate",
                payload={"response": '"A cinematic shot without ending quote'},
            )

            result = await expander.expand_prompt("test")

        # Leading quote should remain since there's no matching trailing quote
        assert result.startswith('"')

    async def test_sends_correct_payload(self):
        expander = self._make_expander()

        with aioresponses() as m:
            m.post(
                "http://test-ollama:11434/api/generate",
                payload={"response": "expanded"},
            )

            await expander.expand_prompt("cat")

            # Verify the request payload — find the POST request in m.requests
            found = False
            for key, calls in m.requests.items():
                method, url = key
                if str(method) == "POST" and "api/generate" in str(url):
                    request_body = calls[0].kwargs["json"]
                    assert request_body["model"] == "gemma3:12b"
                    assert request_body["stream"] is False
                    assert request_body["keep_alive"] == 0
                    assert "cat" in request_body["prompt"]
                    found = True
                    break
            assert found, "POST to /api/generate not found in requests"

    async def test_http_error_raises_exception(self):
        expander = self._make_expander()

        with aioresponses() as m:
            m.post(
                "http://test-ollama:11434/api/generate",
                status=500,
            )

            with pytest.raises(Exception, match="Ollama API error: 500"):
                await expander.expand_prompt("test")

    async def test_empty_response(self):
        expander = self._make_expander()

        with aioresponses() as m:
            m.post(
                "http://test-ollama:11434/api/generate",
                payload={"response": ""},
            )

            result = await expander.expand_prompt("test")

        assert result == ""

    async def test_whitespace_stripped(self):
        expander = self._make_expander()

        with aioresponses() as m:
            m.post(
                "http://test-ollama:11434/api/generate",
                payload={"response": "  expanded prompt with spaces  \n"},
            )

            result = await expander.expand_prompt("test")

        assert result == "expanded prompt with spaces"
