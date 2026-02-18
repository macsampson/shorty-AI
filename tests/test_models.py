import pytest
from pydantic import ValidationError


class TestVideoGenerationStatus:
    def test_defaults(self):
        from api.models import VideoGenerationStatus
        status = VideoGenerationStatus(job_id="abc-123", status="started")
        assert status.job_id == "abc-123"
        assert status.status == "started"
        assert status.progress == 0.0
        assert status.stage == ""
        assert status.message == ""
        assert status.video_url is None

    def test_all_fields(self):
        from api.models import VideoGenerationStatus
        status = VideoGenerationStatus(
            job_id="job-1",
            status="complete",
            progress=100.0,
            stage="complete",
            message="Done!",
            video_url="/videos/test.mp4",
        )
        assert status.progress == 100.0
        assert status.video_url == "/videos/test.mp4"

    def test_missing_required_fields(self):
        from api.models import VideoGenerationStatus
        with pytest.raises(ValidationError):
            VideoGenerationStatus()


class TestGenerateTextRequest:
    def test_required_prompt(self):
        from api.schemas.generate_text_request import GenerateTextRequest
        with pytest.raises(ValidationError):
            GenerateTextRequest()

    def test_prompt_only(self):
        from api.schemas.generate_text_request import GenerateTextRequest
        req = GenerateTextRequest(prompt="cat on a street")
        assert req.prompt == "cat on a street"
        assert req.max_length == 200
        assert req.num_return_sequences == 1

    def test_custom_values(self):
        from api.schemas.generate_text_request import GenerateTextRequest
        req = GenerateTextRequest(prompt="test", max_length=500, num_return_sequences=3)
        assert req.max_length == 500
        assert req.num_return_sequences == 3
