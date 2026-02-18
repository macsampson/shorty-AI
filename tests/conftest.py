import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def override_settings(monkeypatch, tmp_path):
    """Prevent tests from hitting real services by overriding settings."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://test-ollama:11434")
    monkeypatch.setenv("COMFYUI_BASE_URL", "http://test-comfyui:8188")
    monkeypatch.setenv("COMFYUI_OUTPUT_DIR", str(tmp_path / "comfyui_output"))
    monkeypatch.setenv("WHISPER_MODEL_SIZE", "base")
    monkeypatch.setenv("SINGLE_GPU_MODE", "false")
    monkeypatch.setenv("VIDIGEN_FRAME_COUNT", "121")

    # Re-create settings with overridden env vars
    from api.config import Settings
    test_settings = Settings()
    monkeypatch.setattr("api.config.settings", test_settings)
    return test_settings


@pytest.fixture
def single_gpu_settings(monkeypatch, tmp_path):
    """Settings with single_gpu_mode enabled."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://test-ollama:11434")
    monkeypatch.setenv("COMFYUI_BASE_URL", "http://test-comfyui:8188")
    monkeypatch.setenv("COMFYUI_OUTPUT_DIR", str(tmp_path / "comfyui_output"))
    monkeypatch.setenv("WHISPER_MODEL_SIZE", "base")
    monkeypatch.setenv("SINGLE_GPU_MODE", "true")
    monkeypatch.setenv("VIDIGEN_FRAME_COUNT", "121")

    from api.config import Settings
    test_settings = Settings()
    monkeypatch.setattr("api.config.settings", test_settings)
    return test_settings


@pytest.fixture
def sample_word_timestamps():
    """Realistic word-level timestamps from Whisper."""
    return [
        {"text": "A", "start": 0.0, "end": 0.15},
        {"text": "woman", "start": 0.15, "end": 0.45},
        {"text": "walks", "start": 0.45, "end": 0.72},
        {"text": "through", "start": 0.72, "end": 0.95},
        {"text": "the", "start": 0.95, "end": 1.05},
        {"text": "rain", "start": 1.05, "end": 1.35},
        {"text": "soaked", "start": 1.35, "end": 1.68},
        {"text": "streets", "start": 1.68, "end": 2.01},
        {"text": "of", "start": 2.01, "end": 2.12},
        {"text": "Tokyo", "start": 2.12, "end": 2.55},
        {"text": "at", "start": 2.55, "end": 2.65},
        {"text": "midnight", "start": 2.65, "end": 3.10},
    ]


@pytest.fixture
def sample_workflow():
    """Load the real ComfyUI workflow template."""
    workflow_path = Path(__file__).parent.parent / "comfyui_workflows" / "video_ltx2_t2v_distilled_api.json"
    with open(workflow_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Temporary directory for file-producing tests."""
    output = tmp_path / "output"
    output.mkdir()
    return output
