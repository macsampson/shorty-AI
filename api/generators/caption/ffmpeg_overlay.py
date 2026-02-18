import subprocess
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class FFmpegCaptionOverlay:
    """Overlay word-level captions on video using FFmpeg ASS subtitles"""

    def __init__(self):
        self.style_config = {
            "font_name": "Arial",
            "font_size": 48,
            "primary_color": "&H00FFFFFF",  # White
            "highlight_color": "&H0000FF7F",  # Green
            "outline_color": "&H00000000",  # Black
            "back_color": "&H80000000",  # Semi-transparent black
            "bold": -1,
            "border_style": 1,
            "outline": 2,
            "shadow": 1,
            "alignment": 2,  # Bottom center
            "margin_v": 50
        }

    def _create_ass_file(self, word_timestamps: List[Dict[str, Any]], output_path: str) -> str:
        """Generate ASS subtitle file with word-level highlighting"""

        ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{self.style_config['font_name']},{self.style_config['font_size']},{self.style_config['primary_color']},{self.style_config['primary_color']},{self.style_config['outline_color']},{self.style_config['back_color']},{self.style_config['bold']},0,0,0,100,100,0,0,{self.style_config['border_style']},{self.style_config['outline']},{self.style_config['shadow']},{self.style_config['alignment']},10,10,{self.style_config['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        ass_events = []

        # Group words into phrases (max 5 words per line for readability)
        words_per_line = 5

        for i in range(0, len(word_timestamps), words_per_line):
            phrase_words = word_timestamps[i:i + words_per_line]

            # For each word in the phrase, create a highlighted version
            for j, word_data in enumerate(phrase_words):
                start_time = self._format_ass_time(word_data["start"])
                end_time = self._format_ass_time(word_data["end"])

                # Build the phrase with current word highlighted
                phrase_parts = []
                for k, w in enumerate(phrase_words):
                    if k == j:
                        # Highlight current word
                        phrase_parts.append(f"{{\\c{self.style_config['highlight_color']}}}{w['text']}{{\\c}}")
                    else:
                        # Normal color
                        phrase_parts.append(w["text"])

                phrase_text = " ".join(phrase_parts)

                ass_events.append(
                    f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{phrase_text}"
                )

        # Write ASS file
        ass_content = ass_header + "\n".join(ass_events)
        ass_file_path = output_path.replace(".mp4", ".ass")

        with open(ass_file_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        logger.info(f"[ASS] Written {len(ass_events)} dialogue lines to {ass_file_path}")

        return ass_file_path

    def _format_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format: H:MM:SS.CC"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)

        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    def _check_nvenc_available(self) -> bool:
        """Check if h264_nvenc encoder is available in this FFmpeg build"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-encoders"],
                capture_output=True, text=True, timeout=10
            )
            return "h264_nvenc" in result.stdout
        except Exception:
            return False

    async def overlay_captions(
        self,
        video_path: str,
        word_timestamps: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """
        Overlay captions on video using FFmpeg

        Args:
            video_path: Path to input video (with audio from LTX-2)
            word_timestamps: Word-level timestamp data from Whisper
            output_path: Path for output video with captions

        Returns:
            Path to final video with captions overlaid
        """

        # Generate ASS subtitle file
        ass_file = self._create_ass_file(word_timestamps, output_path)

        # Select encoder: prefer GPU (h264_nvenc), fall back to CPU (libx264)
        if self._check_nvenc_available():
            encoder = "h264_nvenc"
            preset = "fast"
        else:
            encoder = "libx264"
            preset = "ultrafast"

        # Run FFmpeg from the ASS file's directory so the filter path has no
        # drive-letter colon (which FFmpeg's filter parser misinterprets).
        ass_dir = os.path.dirname(ass_file)
        ass_filename = os.path.basename(ass_file)

        ffmpeg_cmd = [
            "ffmpeg",
            "-i", os.path.abspath(video_path),
            "-vf", f"ass={ass_filename}",
            "-c:v", encoder,
            "-preset", preset,
            "-c:a", "copy",
            "-y",
            os.path.abspath(output_path)
        ]

        logger.info(f"[FFmpeg] Command: {' '.join(ffmpeg_cmd)}")
        logger.info(f"[FFmpeg] Working dir: {ass_dir}")
        logger.info(f"[FFmpeg] Encoder: {encoder}")

        # Execute FFmpeg from the ASS file's directory
        process = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            cwd=ass_dir
        )

        if process.returncode != 0:
            # Log stderr but keep ASS file for debugging
            logger.error(f"[FFmpeg] stderr:\n{process.stderr}")
            raise Exception(f"FFmpeg caption overlay failed: {process.stderr}")

        logger.info(f"[FFmpeg] Overlay complete: {output_path}")

        # Store which encoder was used (useful for diagnostics)
        self.last_encoder = encoder

        return output_path
