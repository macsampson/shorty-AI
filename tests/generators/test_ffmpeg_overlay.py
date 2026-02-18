import os
import pytest
from unittest.mock import patch, MagicMock
from api.generators.caption.ffmpeg_overlay import FFmpegCaptionOverlay


class TestFormatAssTime:
    def setup_method(self):
        self.overlay = FFmpegCaptionOverlay()

    def test_zero_seconds(self):
        assert self.overlay._format_ass_time(0.0) == "0:00:00.00"

    def test_fractional_seconds(self):
        assert self.overlay._format_ass_time(1.55) == "0:00:01.55"

    def test_thirty_seconds(self):
        assert self.overlay._format_ass_time(30.0) == "0:00:30.00"

    def test_minutes(self):
        assert self.overlay._format_ass_time(65.5) == "0:01:05.50"

    def test_hours(self):
        assert self.overlay._format_ass_time(3661.25) == "1:01:01.25"

    def test_small_fraction(self):
        assert self.overlay._format_ass_time(0.05) == "0:00:00.05"

    def test_99_centiseconds(self):
        assert self.overlay._format_ass_time(0.99) == "0:00:00.99"


class TestCreateAssFile:
    def setup_method(self):
        self.overlay = FFmpegCaptionOverlay()

    def test_creates_ass_file(self, sample_word_timestamps, tmp_output_dir):
        output_path = str(tmp_output_dir / "video.mp4")
        ass_path = self.overlay._create_ass_file(sample_word_timestamps, output_path)

        assert ass_path.endswith(".ass")
        assert os.path.exists(ass_path)

    def test_ass_header_format(self, sample_word_timestamps, tmp_output_dir):
        output_path = str(tmp_output_dir / "video.mp4")
        ass_path = self.overlay._create_ass_file(sample_word_timestamps, output_path)

        with open(ass_path, "r") as f:
            content = f.read()

        assert "[Script Info]" in content
        assert "ScriptType: v4.00+" in content
        assert "[V4+ Styles]" in content
        assert "[Events]" in content
        assert "Style: Default,Arial,48" in content

    def test_five_word_grouping(self, sample_word_timestamps, tmp_output_dir):
        """12 words → 3 groups: [5, 5, 2] words."""
        output_path = str(tmp_output_dir / "video.mp4")
        ass_path = self.overlay._create_ass_file(sample_word_timestamps, output_path)

        with open(ass_path, "r") as f:
            content = f.read()

        dialogue_lines = [l for l in content.split("\n") if l.startswith("Dialogue:")]
        # 5 highlight events for group 1 + 5 for group 2 + 2 for group 3 = 12
        assert len(dialogue_lines) == 12

    def test_word_highlighting(self, tmp_output_dir):
        """Current word should use highlight color."""
        words = [
            {"text": "hello", "start": 0.0, "end": 0.5},
            {"text": "world", "start": 0.5, "end": 1.0},
        ]
        output_path = str(tmp_output_dir / "video.mp4")
        ass_path = self.overlay._create_ass_file(words, output_path)

        with open(ass_path, "r") as f:
            content = f.read()

        dialogue_lines = [l for l in content.split("\n") if l.startswith("Dialogue:")]
        # First line: "hello" highlighted, "world" normal
        assert "{\\c&H0000FF7F}hello{\\c}" in dialogue_lines[0]
        assert "world" in dialogue_lines[0]
        # Second line: "hello" normal, "world" highlighted
        assert "hello" in dialogue_lines[1]
        assert "{\\c&H0000FF7F}world{\\c}" in dialogue_lines[1]

    def test_correct_timestamps_in_dialogue(self, tmp_output_dir):
        words = [
            {"text": "test", "start": 1.5, "end": 2.0},
        ]
        output_path = str(tmp_output_dir / "video.mp4")
        ass_path = self.overlay._create_ass_file(words, output_path)

        with open(ass_path, "r") as f:
            content = f.read()

        assert "0:00:01.50,0:00:02.00" in content

    def test_empty_timestamps(self, tmp_output_dir):
        output_path = str(tmp_output_dir / "video.mp4")
        ass_path = self.overlay._create_ass_file([], output_path)

        with open(ass_path, "r") as f:
            content = f.read()

        dialogue_lines = [l for l in content.split("\n") if l.startswith("Dialogue:")]
        assert len(dialogue_lines) == 0


class TestCheckNvencAvailable:
    def setup_method(self):
        self.overlay = FFmpegCaptionOverlay()

    @patch("api.generators.caption.ffmpeg_overlay.subprocess.run")
    def test_nvenc_available(self, mock_run):
        mock_run.return_value = MagicMock(stdout="... h264_nvenc ...")
        assert self.overlay._check_nvenc_available() is True

    @patch("api.generators.caption.ffmpeg_overlay.subprocess.run")
    def test_nvenc_not_available(self, mock_run):
        mock_run.return_value = MagicMock(stdout="... libx264 ...")
        assert self.overlay._check_nvenc_available() is False

    @patch("api.generators.caption.ffmpeg_overlay.subprocess.run", side_effect=FileNotFoundError)
    def test_ffmpeg_missing(self, mock_run):
        assert self.overlay._check_nvenc_available() is False

    @patch("api.generators.caption.ffmpeg_overlay.subprocess.run", side_effect=TimeoutError)
    def test_timeout(self, mock_run):
        assert self.overlay._check_nvenc_available() is False


class TestOverlayCaptions:
    def setup_method(self):
        self.overlay = FFmpegCaptionOverlay()

    @patch("api.generators.caption.ffmpeg_overlay.os.remove")
    @patch("api.generators.caption.ffmpeg_overlay.subprocess.run")
    @patch.object(FFmpegCaptionOverlay, "_check_nvenc_available", return_value=True)
    @patch.object(FFmpegCaptionOverlay, "_create_ass_file", return_value="/tmp/test.ass")
    async def test_uses_nvenc_when_available(self, mock_ass, mock_nvenc, mock_run, mock_remove):
        mock_run.return_value = MagicMock(returncode=0)

        result = await self.overlay.overlay_captions("input.mp4", [], "output.mp4")

        call_args = mock_run.call_args[0][0]
        assert "h264_nvenc" in call_args
        assert "fast" in call_args
        assert result == "output.mp4"

    @patch("api.generators.caption.ffmpeg_overlay.os.remove")
    @patch("api.generators.caption.ffmpeg_overlay.subprocess.run")
    @patch.object(FFmpegCaptionOverlay, "_check_nvenc_available", return_value=False)
    @patch.object(FFmpegCaptionOverlay, "_create_ass_file", return_value="/tmp/test.ass")
    async def test_falls_back_to_libx264(self, mock_ass, mock_nvenc, mock_run, mock_remove):
        mock_run.return_value = MagicMock(returncode=0)

        await self.overlay.overlay_captions("input.mp4", [], "output.mp4")

        call_args = mock_run.call_args[0][0]
        assert "libx264" in call_args
        assert "ultrafast" in call_args

    @patch("api.generators.caption.ffmpeg_overlay.os.remove")
    @patch("api.generators.caption.ffmpeg_overlay.subprocess.run")
    @patch.object(FFmpegCaptionOverlay, "_check_nvenc_available", return_value=True)
    @patch.object(FFmpegCaptionOverlay, "_create_ass_file", return_value="C:\\videos\\test.ass")
    async def test_windows_path_escaping(self, mock_ass, mock_nvenc, mock_run, mock_remove):
        mock_run.return_value = MagicMock(returncode=0)

        await self.overlay.overlay_captions("input.mp4", [], "output.mp4")

        call_args = mock_run.call_args[0][0]
        vf_arg = call_args[call_args.index("-vf") + 1]
        # Backslashes should be forward slashes, colons escaped
        assert "\\" not in vf_arg.replace("\\:", "")
        assert "C\\:" in vf_arg  # colon escaped

    @patch("api.generators.caption.ffmpeg_overlay.subprocess.run")
    @patch.object(FFmpegCaptionOverlay, "_check_nvenc_available", return_value=True)
    @patch.object(FFmpegCaptionOverlay, "_create_ass_file", return_value="/tmp/test.ass")
    async def test_raises_on_ffmpeg_failure(self, mock_ass, mock_nvenc, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="encoding error")

        with pytest.raises(Exception, match="FFmpeg caption overlay failed"):
            await self.overlay.overlay_captions("input.mp4", [], "output.mp4")

    @patch("api.generators.caption.ffmpeg_overlay.os.remove")
    @patch("api.generators.caption.ffmpeg_overlay.subprocess.run")
    @patch.object(FFmpegCaptionOverlay, "_check_nvenc_available", return_value=True)
    @patch.object(FFmpegCaptionOverlay, "_create_ass_file", return_value="/tmp/test.ass")
    async def test_cleans_up_ass_file(self, mock_ass, mock_nvenc, mock_run, mock_remove):
        mock_run.return_value = MagicMock(returncode=0)

        await self.overlay.overlay_captions("input.mp4", [], "output.mp4")

        mock_remove.assert_called_once_with("/tmp/test.ass")
