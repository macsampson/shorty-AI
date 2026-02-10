
import sys
from unittest.mock import MagicMock, AsyncMock

# --- MOCKING DEPENDENCIES BEFORE IMPORT ---
# We mock these because they might not be installed in the environment running this script.

# Mock pydantic
mock_pydantic = MagicMock()
mock_base_model = MagicMock
mock_pydantic.BaseModel = mock_base_model
sys.modules["pydantic"] = mock_pydantic

# Mock pydantic_settings
mock_pydantic_settings = MagicMock()
mock_pydantic_settings.BaseSettings = MagicMock
mock_pydantic_settings.SettingsConfigDict = MagicMock
sys.modules["pydantic_settings"] = mock_pydantic_settings

# Mock fastapi
mock_fastapi = MagicMock()
class MockHTTPException(Exception):
    def __init__(self, status_code, detail=None):
        self.status_code = status_code
        self.detail = detail
mock_fastapi.HTTPException = MockHTTPException
sys.modules["fastapi"] = mock_fastapi

# Mock aiohttp (we use it in the code)
# We can let it be imported if installed, or mock it if not.
# It is likely installed, but let's mock it to be safe and use AsyncMock for sessions.
mock_aiohttp = MagicMock()
mock_client_session = MagicMock()
mock_aiohttp.ClientSession = mock_client_session
sys.modules["aiohttp"] = mock_aiohttp

# --- MOCKING PROJECT CONFIG ---
# We need to inject our own settings before importing the generators
mock_config = MagicMock()
class MockSettings:
    single_gpu_mode = False
    ollama_base_url = "http://mock-ollama"
    ollama_model = "mock-model"
    flux_api_url = "http://mock-flux"
    openai_api_key = "mock"
    elevenlabs_api_key = "mock"

settings_instance = MockSettings()
mock_config.settings = settings_instance
sys.modules["api.config"] = mock_config

# --- REAL IMPORTS (Now safe) ---
# We need to make sure we don't fail on imports inside the modules
# api.generators.base imports ABC, abstractmethod (std lib), pydantic (mocked)
# api.generators.script.ollama_generator imports aiohttp (mocked), fastapi (mocked), config (mocked), base (safe)

import unittest
import asyncio

# Now we can import the classes under test.
# We might need to handle relative imports if not running as module.
# To make imports work like "from api.generators...", we need to ensure the python path is correct.
# The user ran this from project root, so "api" should be found.
# BUT, we already mocked "api.config", so "from api.config import settings" will get our mock.

# However, we need to import specific files.
# Since we are running this script directly, we might need to modify sys.path if not in root.
import os
sys.path.append(os.getcwd())

# We need to manually load the modules or just import them if sys.path is correct.
try:
    from api.generators.script.ollama_generator import OllamaScriptGenerator
    from api.generators.image.flux_generator import FluxImageGenerator
except ImportError as e:
    print(f"Failed to import generators: {e}")
    sys.exit(1)

# --- TESTS ---

class TestSingleGPULogic(unittest.TestCase):
    
    def setUp(self):
        # Reset settings before each test
        settings_instance.single_gpu_mode = False

    def _mock_async_context_manager(self, cm_mock, yielded_value):
        cm_mock.__aenter__ = AsyncMock(return_value=yielded_value)
        cm_mock.__aexit__ = AsyncMock(return_value=None)
        return cm_mock

    def test_ollama_sequential(self):
        # Enable single GPU mode
        settings_instance.single_gpu_mode = True
        
        generator = OllamaScriptGenerator()
        
        session_mock = MagicMock()
        # mock_client_session.return_value is the CM
        self._mock_async_context_manager(mock_client_session.return_value, session_mock)
        
        post_context = MagicMock()
        session_mock.post.return_value = post_context
        
        response_mock = AsyncMock()
        response_mock.status = 200
        response_mock.json.return_value = {"response": '{"title": "Test", "scenes": []}'}
        
        self._mock_async_context_manager(post_context, response_mock)
        
        # Run the async method
        try:
            asyncio.run(generator.generate_script("test"))
        except MockHTTPException as e:
            self.fail(f"Ollama generation failed: {e.detail}")
        
        # Check arguments passed to post
        call_args = session_mock.post.call_args
        self.assertIsNotNone(call_args)
        kwargs = call_args[1]
        json_body = kwargs["json"]
        
        self.assertEqual(json_body.get("keep_alive"), 0, "keep_alive should be 0 for single_gpu_mode")

    def test_ollama_parallel(self):
        # Disable single GPU mode
        settings_instance.single_gpu_mode = False
        
        generator = OllamaScriptGenerator()
        
        session_mock = MagicMock()
        self._mock_async_context_manager(mock_client_session.return_value, session_mock)
        
        post_context = MagicMock()
        session_mock.post.return_value = post_context
        
        response_mock = AsyncMock()
        response_mock.status = 200
        response_mock.json.return_value = {"response": '{"title": "Test", "scenes": []}'}
        
        self._mock_async_context_manager(post_context, response_mock)
        
        try:
            asyncio.run(generator.generate_script("test"))
        except MockHTTPException as e:
            self.fail(f"Ollama generation failed: {e.detail}")
        
        call_args = session_mock.post.call_args
        kwargs = call_args[1]
        json_body = kwargs["json"]
        
        self.assertEqual(json_body.get("keep_alive"), -1, "keep_alive should be -1 for multi_gpu_mode")

    def test_flux_sequential_unloading(self):
        settings_instance.single_gpu_mode = True
        
        generator = FluxImageGenerator()
        
        session_mock = MagicMock()
        self._mock_async_context_manager(mock_client_session.return_value, session_mock)
        
        # We need session.post to return different context managers on consecutive calls
        
        response_gen = AsyncMock()
        response_gen.status = 200
        response_gen.json.return_value = {"image": "base64..."}
        
        response_unload = AsyncMock()
        response_unload.status = 200
        
        context_gen = MagicMock()
        self._mock_async_context_manager(context_gen, response_gen)
        
        context_unload = MagicMock()
        self._mock_async_context_manager(context_unload, response_unload)
        
        session_mock.post.side_effect = [context_gen, context_unload]
        
        # Need to mock base64.b64decode and open
        with unittest.mock.patch("base64.b64decode"), \
             unittest.mock.patch("builtins.open", unittest.mock.mock_open()), \
             unittest.mock.patch("os.makedirs"):
            
            asyncio.run(generator.generate_image("prompt", "/tmp"))
            
        self.assertEqual(session_mock.post.call_count, 2)
        
        # Check URLs
        call1 = session_mock.post.call_args_list[0]
        call2 = session_mock.post.call_args_list[1]
        
        self.assertTrue("generate_image" in call1[0][0])
        self.assertTrue("unload_model" in call2[0][0])

if __name__ == '__main__':
    unittest.main()
