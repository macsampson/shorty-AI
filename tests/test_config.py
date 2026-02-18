import pytest


class TestSettings:
    def test_default_ollama_url(self, override_settings):
        assert override_settings.ollama_base_url == "http://test-ollama:11434"

    def test_default_ollama_model(self):
        from api.config import Settings
        s = Settings(ollama_base_url="http://x:1")
        assert s.ollama_model == "gemma3:12b"

    def test_default_comfyui_url(self, override_settings):
        assert override_settings.comfyui_base_url == "http://test-comfyui:8188"

    def test_default_whisper_model_size(self, override_settings):
        assert override_settings.whisper_model_size == "base"

    def test_default_frame_count(self, override_settings):
        assert override_settings.vidigen_frame_count == 121

    def test_default_single_gpu_mode(self, override_settings):
        assert override_settings.single_gpu_mode is False

    def test_env_override_frame_count(self, monkeypatch):
        monkeypatch.setenv("VIDIGEN_FRAME_COUNT", "161")
        from api.config import Settings
        s = Settings()
        assert s.vidigen_frame_count == 161

    def test_env_override_single_gpu_true(self, monkeypatch):
        monkeypatch.setenv("SINGLE_GPU_MODE", "true")
        from api.config import Settings
        s = Settings()
        assert s.single_gpu_mode is True

    def test_env_override_whisper_model(self, monkeypatch):
        monkeypatch.setenv("WHISPER_MODEL_SIZE", "large")
        from api.config import Settings
        s = Settings()
        assert s.whisper_model_size == "large"
