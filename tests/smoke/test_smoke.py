import os
import subprocess
import pytest
import httpx
from pathlib import Path
from api.config import settings

pytestmark = pytest.mark.smoke

TIMEOUT = 5.0


class TestServiceConnectivity:
    def test_ollama_reachable(self):
        """Ollama API should respond to tag listing."""
        response = httpx.get(
            f"{settings.ollama_base_url}/api/tags", timeout=TIMEOUT
        )
        assert response.status_code == 200

    def test_comfyui_reachable(self):
        """ComfyUI should respond to system stats."""
        response = httpx.get(
            f"{settings.comfyui_base_url}/system_stats", timeout=TIMEOUT
        )
        assert response.status_code == 200

    def test_api_reachable(self):
        """VidiGen API should respond to VRAM status."""
        response = httpx.get("http://localhost:8000/vram_status", timeout=TIMEOUT)
        assert response.status_code == 200

    def test_frontend_reachable(self):
        """Frontend dev server should respond."""
        response = httpx.get("http://localhost:3000/", timeout=TIMEOUT)
        assert response.status_code == 200


class TestFileSystem:
    def test_workflow_file_exists(self):
        """LTX-2 workflow JSON must exist on disk."""
        workflow_path = (
            Path(__file__).parent.parent.parent
            / "comfyui_workflows"
            / "video_ltx2_t2v_distilled_api.json"
        )
        assert workflow_path.exists(), f"Workflow not found: {workflow_path}"

    def test_comfyui_output_dir_exists(self):
        """ComfyUI output directory must be accessible."""
        assert os.path.isdir(
            settings.comfyui_output_dir
        ), f"ComfyUI output dir not found: {settings.comfyui_output_dir}"


class TestTools:
    def test_ffmpeg_available(self):
        """FFmpeg must be installed and on PATH."""
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "ffmpeg version" in result.stdout
