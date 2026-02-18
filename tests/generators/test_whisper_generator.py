import pytest
from unittest.mock import patch, MagicMock


class TestWhisperCaptionGenerator:
    def _make_generator(self):
        with patch("api.generators.caption.whisper_generator.settings") as mock_settings:
            mock_settings.whisper_model_size = "base"
            mock_settings.whisper_min_confidence = 0.4
            mock_settings.whisper_no_speech_threshold = 0.3
            mock_settings.single_gpu_mode = False
            from api.generators.caption.whisper_generator import WhisperCaptionGenerator
            gen = WhisperCaptionGenerator()
        return gen

    @patch("api.generators.caption.whisper_generator.whisper")
    async def test_returns_word_timestamps(self, mock_whisper):
        gen = self._make_generator()

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [
                {
                    "no_speech_prob": 0.01,
                    "words": [
                        {"word": " hello", "start": 0.0, "end": 0.5, "probability": 0.95},
                        {"word": " world", "start": 0.5, "end": 1.0, "probability": 0.90},
                    ]
                }
            ]
        }
        gen.model = mock_model

        result = await gen.generate_captions("test.mp4")

        assert len(result) == 2
        assert result[0] == {"text": "hello", "start": 0.0, "end": 0.5}
        assert result[1] == {"text": "world", "start": 0.5, "end": 1.0}

    @patch("api.generators.caption.whisper_generator.whisper")
    async def test_strips_whitespace_from_words(self, mock_whisper):
        gen = self._make_generator()

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [
                {
                    "no_speech_prob": 0.01,
                    "words": [{"word": "  padded  ", "start": 0.0, "end": 0.5, "probability": 0.9}],
                }
            ]
        }
        gen.model = mock_model

        result = await gen.generate_captions("test.mp4")
        assert result[0]["text"] == "padded"

    @patch("api.generators.caption.whisper_generator.whisper")
    async def test_handles_empty_segments(self, mock_whisper):
        gen = self._make_generator()

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"segments": []}
        gen.model = mock_model

        result = await gen.generate_captions("test.mp4")
        assert result == []

    @patch("api.generators.caption.whisper_generator.whisper")
    async def test_handles_segments_without_words(self, mock_whisper):
        gen = self._make_generator()

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [{"text": "hello world", "no_speech_prob": 0.01}]  # No "words" key
        }
        gen.model = mock_model

        result = await gen.generate_captions("test.mp4")
        assert result == []

    @patch("api.generators.caption.whisper_generator.whisper")
    async def test_lazy_loads_model(self, mock_whisper):
        gen = self._make_generator()
        assert gen.model is None

        mock_whisper.load_model.return_value = MagicMock(
            transcribe=MagicMock(return_value={"segments": []})
        )

        await gen.generate_captions("test.mp4")

        mock_whisper.load_model.assert_called_once_with("base")

    @patch("api.generators.caption.whisper_generator.whisper")
    async def test_does_not_reload_model(self, mock_whisper):
        gen = self._make_generator()
        gen.model = MagicMock(
            transcribe=MagicMock(return_value={"segments": []})
        )

        await gen.generate_captions("test.mp4")

        mock_whisper.load_model.assert_not_called()

    @patch("api.generators.caption.whisper_generator.settings")
    @patch("api.generators.caption.whisper_generator.torch")
    @patch("api.generators.caption.whisper_generator.whisper")
    async def test_unloads_model_in_single_gpu_mode(self, mock_whisper, mock_torch, mock_settings):
        mock_settings.single_gpu_mode = True
        mock_settings.whisper_model_size = "base"
        mock_settings.whisper_min_confidence = 0.4
        mock_settings.whisper_no_speech_threshold = 0.3
        mock_torch.cuda.is_available.return_value = True

        from api.generators.caption.whisper_generator import WhisperCaptionGenerator
        gen = WhisperCaptionGenerator()
        gen.model = MagicMock(
            transcribe=MagicMock(return_value={"segments": []})
        )

        await gen.generate_captions("test.mp4")

        assert gen.model is None
        mock_torch.cuda.empty_cache.assert_called_once()
        mock_torch.cuda.synchronize.assert_called_once()

    @patch("api.generators.caption.whisper_generator.settings")
    @patch("api.generators.caption.whisper_generator.whisper")
    async def test_keeps_model_in_multi_gpu_mode(self, mock_whisper, mock_settings):
        mock_settings.single_gpu_mode = False
        mock_settings.whisper_model_size = "base"
        mock_settings.whisper_min_confidence = 0.4
        mock_settings.whisper_no_speech_threshold = 0.3

        from api.generators.caption.whisper_generator import WhisperCaptionGenerator
        gen = WhisperCaptionGenerator()
        mock_model = MagicMock(
            transcribe=MagicMock(return_value={"segments": []})
        )
        gen.model = mock_model

        await gen.generate_captions("test.mp4")

        assert gen.model is mock_model  # Should NOT be unloaded

    @patch("api.generators.caption.whisper_generator.whisper")
    async def test_multiple_segments(self, mock_whisper):
        gen = self._make_generator()

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [
                {"no_speech_prob": 0.01, "words": [{"word": "hello", "start": 0.0, "end": 0.5, "probability": 0.9}]},
                {"no_speech_prob": 0.01, "words": [{"word": "world", "start": 1.0, "end": 1.5, "probability": 0.9}]},
            ]
        }
        gen.model = mock_model

        result = await gen.generate_captions("test.mp4")
        assert len(result) == 2
        assert result[0]["text"] == "hello"
        assert result[1]["text"] == "world"

    @patch("api.generators.caption.whisper_generator.whisper")
    async def test_filters_low_confidence_words(self, mock_whisper):
        gen = self._make_generator()

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [
                {
                    "no_speech_prob": 0.01,
                    "words": [
                        {"word": "hello", "start": 0.0, "end": 0.5, "probability": 0.9},
                        {"word": "um", "start": 0.5, "end": 0.7, "probability": 0.15},
                        {"word": "world", "start": 0.7, "end": 1.0, "probability": 0.85},
                    ]
                }
            ]
        }
        gen.model = mock_model

        result = await gen.generate_captions("test.mp4")
        assert len(result) == 2
        assert result[0]["text"] == "hello"
        assert result[1]["text"] == "world"

    @patch("api.generators.caption.whisper_generator.whisper")
    async def test_skips_high_no_speech_prob_segments(self, mock_whisper):
        gen = self._make_generator()

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [
                {
                    "no_speech_prob": 0.95,  # Very likely not speech
                    "text": "hallucinated text",
                    "words": [
                        {"word": "hallucinated", "start": 0.0, "end": 0.5, "probability": 0.5},
                        {"word": "text", "start": 0.5, "end": 1.0, "probability": 0.5},
                    ]
                }
            ]
        }
        gen.model = mock_model

        result = await gen.generate_captions("test.mp4")
        assert result == []

    @patch("api.generators.caption.whisper_generator.whisper")
    async def test_all_words_filtered_returns_empty(self, mock_whisper):
        """When all words are low confidence, result should be empty (pipeline skips overlay)"""
        gen = self._make_generator()

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [
                {
                    "no_speech_prob": 0.1,
                    "words": [
                        {"word": "uh", "start": 0.0, "end": 0.3, "probability": 0.1},
                        {"word": "mm", "start": 0.3, "end": 0.6, "probability": 0.05},
                    ]
                }
            ]
        }
        gen.model = mock_model

        result = await gen.generate_captions("test.mp4")
        assert result == []

    @patch("api.generators.caption.whisper_generator.whisper")
    async def test_passes_correct_transcribe_params(self, mock_whisper):
        gen = self._make_generator()

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"segments": []}
        gen.model = mock_model

        await gen.generate_captions("test.mp4")

        mock_model.transcribe.assert_called_once_with(
            "test.mp4",
            task="transcribe",
            language="en",
            word_timestamps=True,
            verbose=False,
            no_speech_threshold=0.3,
            logprob_threshold=-0.5,
            condition_on_previous_text=False,
        )
