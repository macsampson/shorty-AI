import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from api.main import app


def duration_to_frame_count(seconds: int) -> int:
    """Replicate the pipeline's conversion: snap to nearest 8n+1"""
    raw_frames = seconds * 24
    return (raw_frames // 8) * 8 + 1


class TestDurationToFrameCount:
    """Verify the duration-to-frame-count formula produces valid 8n+1 values"""

    def test_5_seconds(self):
        assert duration_to_frame_count(5) == 121

    def test_10_seconds(self):
        assert duration_to_frame_count(10) == 241

    def test_15_seconds(self):
        assert duration_to_frame_count(15) == 361

    def test_30_seconds(self):
        assert duration_to_frame_count(30) == 721

    def test_all_valid_durations_produce_8n_plus_1(self):
        """Every integer duration in range must produce a valid 8n+1 frame count"""
        for seconds in range(5, 31):
            frames = duration_to_frame_count(seconds)
            assert (frames - 1) % 8 == 0, f"{seconds}s -> {frames} frames is not 8n+1"


class TestApiDurationSeconds:
    """Test that the /generate_video_vidigen endpoint handles duration_seconds correctly"""

    @pytest.fixture
    def mock_pipeline(self):
        with patch("api.main.run_vidigen_pipeline", new_callable=AsyncMock) as mock:
            yield mock

    async def test_api_accepts_duration_seconds(self, mock_pipeline):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/generate_video_vidigen",
                json={"prompt": "a cat walking", "duration_seconds": 10},
            )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "started"

    async def test_api_defaults_duration_to_5(self, mock_pipeline):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/generate_video_vidigen",
                json={"prompt": "a sunset over mountains"},
            )
        assert response.status_code == 200
        # Pipeline should have been called with duration_seconds=5
        call_args = mock_pipeline.call_args
        assert call_args[0][2] == 5  # third positional arg is duration_seconds

    async def test_api_rejects_duration_below_5(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/generate_video_vidigen",
                json={"prompt": "test", "duration_seconds": 0},
            )
        assert response.status_code == 422

    async def test_api_rejects_duration_above_30(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/generate_video_vidigen",
                json={"prompt": "test", "duration_seconds": 50},
            )
        assert response.status_code == 422
