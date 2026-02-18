import json
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def test_app(tmp_path, monkeypatch):
    """Create a test FastAPI app with monkeypatched directories."""
    monkeypatch.setenv("GENERATIONS_DIR", str(tmp_path / "generations"))

    # Must patch before importing app
    gen_dir = str(tmp_path / "generations")
    videos_dir = os.path.join(gen_dir, "videos")
    os.makedirs(videos_dir, exist_ok=True)

    monkeypatch.setattr("api.main.GENERATIONS_DIR", gen_dir)
    monkeypatch.setattr("api.main.GENERATED_VIDEOS_DIR", videos_dir)

    from api.main import app
    return app, videos_dir


class TestGenerateVideoVidigen:
    @patch("api.main.run_vidigen_pipeline", new_callable=AsyncMock)
    async def test_returns_job_id_and_status(self, mock_pipeline, test_app):
        app, _ = test_app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/generate_video_vidigen",
                json={"prompt": "cat on a street"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "started"
        assert data["pipeline"] == "vidigen"

    async def test_missing_prompt_returns_422(self, test_app):
        app, _ = test_app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/generate_video_vidigen",
                json={},
            )

        assert response.status_code == 422


class TestExpandPrompt:
    @patch("api.main.GeneratorFactory")
    async def test_success(self, mock_factory, test_app):
        app, _ = test_app

        mock_expander = AsyncMock()
        mock_expander.expand_prompt.return_value = "A cinematic shot..."
        mock_factory.get_prompt_expander.return_value = mock_expander

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/expand_prompt",
                json={"prompt": "cat"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["original"] == "cat"
        assert data["expanded"] == "A cinematic shot..."

    @patch("api.main.GeneratorFactory")
    async def test_error_returns_500(self, mock_factory, test_app):
        app, _ = test_app

        mock_expander = AsyncMock()
        mock_expander.expand_prompt.side_effect = Exception("Ollama down")
        mock_factory.get_prompt_expander.return_value = mock_expander

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/expand_prompt",
                json={"prompt": "cat"},
            )

        assert response.status_code == 500
        assert "Ollama down" in response.json()["detail"]


class TestVramStatus:
    @patch("api.main.get_vram_usage")
    async def test_returns_vram_data(self, mock_vram, test_app):
        app, _ = test_app

        mock_vram.return_value = {
            "allocated_gb": 4.0,
            "reserved_gb": 4.0,
            "total_gb": 24.0,
            "free_gb": 20.0,
        }

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/vram_status")

        assert response.status_code == 200
        data = response.json()
        assert data["total_gb"] == 24.0
        assert data["free_gb"] == 20.0


class TestListGeneratedContent:
    async def test_lists_folders(self, test_app):
        app, videos_dir = test_app

        # Create some folders
        os.makedirs(os.path.join(videos_dir, "20250101_120000_job1"))
        os.makedirs(os.path.join(videos_dir, "20250102_120000_job2"))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/list_generated_content")

        assert response.status_code == 200
        folders = response.json()["folders"]
        assert len(folders) == 2

    async def test_empty_directory(self, test_app):
        app, _ = test_app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/list_generated_content")

        assert response.status_code == 200
        assert response.json()["folders"] == []


class TestGetGeneratedContent:
    async def test_returns_metadata_and_videos(self, test_app):
        app, videos_dir = test_app

        folder_name = "20250101_120000_job1"
        folder_path = os.path.join(videos_dir, folder_name)
        os.makedirs(folder_path)

        # Create a video file
        with open(os.path.join(folder_path, "final_job1.mp4"), "w") as f:
            f.write("fake video")

        # Create metadata
        metadata = {"job_id": "job1", "original_prompt": "cat"}
        with open(os.path.join(folder_path, "metadata.json"), "w") as f:
            json.dump(metadata, f)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/get_generated_content/{folder_name}")

        assert response.status_code == 200
        data = response.json()
        assert data["script"]["job_id"] == "job1"
        assert len(data["video_urls"]) == 1
        assert "final_job1.mp4" in data["video_urls"][0]

    async def test_folder_not_found(self, test_app):
        app, _ = test_app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/get_generated_content/nonexistent")

        assert response.status_code == 404

    async def test_folder_without_videos(self, test_app):
        app, videos_dir = test_app

        folder_name = "empty_folder"
        os.makedirs(os.path.join(videos_dir, folder_name))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/get_generated_content/{folder_name}")

        assert response.status_code == 404
