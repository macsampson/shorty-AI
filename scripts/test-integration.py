"""
VidiGen AI - Integration Test Suite
====================================
Tests each pipeline stage sequentially, reports pass/fail per stage.
Run: python scripts/test-integration.py [--keep]
"""

import sys
import os
import time
import asyncio
import argparse
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path so we can import api modules
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)


# ── Helpers ──────────────────────────────────────────────────────────────────

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def print_header():
    print(f"\n{Colors.BOLD}{'=' * 48}")
    print(f"  VidiGen AI - Integration Test Suite")
    print(f"{'=' * 48}{Colors.RESET}\n")


def print_stage(num: int, desc: str):
    print(f"\n{Colors.CYAN}[STAGE {num}]{Colors.RESET} {desc}...")


def print_pass(label: str, elapsed: float):
    print(f"{Colors.GREEN}[PASS]{Colors.RESET} {label} ({elapsed:.1f}s)")


def print_fail(label: str, error: str):
    print(f"{Colors.RED}[FAIL]{Colors.RESET} {label}")
    print(f"  Error: {error}")


def print_detail(key: str, value: str):
    print(f"  {key + ':':12s} {value}")


def format_size(size_bytes: int) -> str:
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.1f} MB"
    elif size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.1f} KB"
    return f"{size_bytes} bytes"


# ── Stage implementations ───────────────────────────────────────────────────

def stage_0_prerequisites() -> dict:
    """Check all prerequisites are available"""
    results = {}

    # FFmpeg
    try:
        proc = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=10
        )
        if proc.returncode == 0:
            version_line = proc.stdout.split("\n")[0]
            version = version_line.split(" ")[2] if len(version_line.split(" ")) >= 3 else "unknown"
            print_detail("FFmpeg", f"OK (version {version})")
            results["ffmpeg"] = True
        else:
            raise Exception("ffmpeg returned non-zero exit code")
    except FileNotFoundError:
        print_detail("FFmpeg", "NOT FOUND - install with: winget install Gyan.FFmpeg")
        results["ffmpeg"] = False
    except Exception as e:
        print_detail("FFmpeg", f"FAILED ({e})")
        results["ffmpeg"] = False

    # ffprobe
    try:
        proc = subprocess.run(
            ["ffprobe", "-version"], capture_output=True, text=True, timeout=10
        )
        results["ffprobe"] = proc.returncode == 0
        print_detail("ffprobe", "OK" if results["ffprobe"] else "NOT FOUND")
    except FileNotFoundError:
        print_detail("ffprobe", "NOT FOUND (should come with FFmpeg)")
        results["ffprobe"] = False

    # Ollama
    import urllib.request
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5)
        if req.status == 200:
            print_detail("Ollama", "OK (http://localhost:11434)")
            results["ollama"] = True
        else:
            raise Exception(f"status {req.status}")
    except Exception as e:
        print_detail("Ollama", f"UNREACHABLE ({e})")
        results["ollama"] = False

    # ComfyUI
    try:
        req = urllib.request.urlopen("http://localhost:8188/system_stats", timeout=5)
        if req.status == 200:
            print_detail("ComfyUI", "OK (http://localhost:8188)")
            results["comfyui"] = True
        else:
            raise Exception(f"status {req.status}")
    except Exception as e:
        print_detail("ComfyUI", f"UNREACHABLE ({e})")
        results["comfyui"] = False

    # Workflow file
    workflow_path = Path("comfyui_workflows/video_ltx2_t2v_distilled_api.json")
    if workflow_path.exists():
        print_detail("Workflow", f"OK ({workflow_path})")
        results["workflow"] = True
    else:
        print_detail("Workflow", f"NOT FOUND ({workflow_path})")
        results["workflow"] = False

    # ComfyUI output directory
    from api.config import settings
    output_dir = Path(settings.comfyui_output_dir)
    if output_dir.exists():
        print_detail("Output dir", f"OK ({output_dir})")
        results["output_dir"] = True
    else:
        print_detail("Output dir", f"NOT FOUND ({output_dir})")
        results["output_dir"] = False

    # Check all passed
    if not all(results.values()):
        failed = [k for k, v in results.items() if not v]
        raise Exception(f"Prerequisites failed: {', '.join(failed)}")

    return results


async def stage_1_prompt_expansion() -> str:
    """Test prompt expansion with Ollama"""
    from api.generators.prompt.ollama_expander import OllamaPromptExpander

    test_prompt = "a cat walking on the street"
    print_detail("Input", f'"{test_prompt}"')

    expander = OllamaPromptExpander()
    expanded = await expander.expand_prompt(test_prompt)

    word_count = len(expanded.split())
    # Show truncated preview
    preview = expanded[:80] + "..." if len(expanded) > 80 else expanded
    print_detail("Output", f'"{preview}" ({word_count} words)')

    if not expanded or word_count < 20:
        raise Exception(
            f"Expanded prompt too short ({word_count} words, expected >20)"
        )

    return expanded


async def stage_2_video_generation(prompt: str, output_dir: str) -> str:
    """Test video generation with ComfyUI/LTX-2"""
    from api.generators.video.comfyui_generator import ComfyUIVideoGenerator

    generator = ComfyUIVideoGenerator()

    # Progress dots
    dot_count = 0

    async def progress_cb(pct: float):
        nonlocal dot_count
        new_dots = int(pct / 10) - dot_count
        if new_dots > 0:
            print("." * new_dots, end="", flush=True)
            dot_count += new_dots

    print("  Progress: ", end="", flush=True)
    video_path = await generator.generate_video(prompt, output_dir, progress_cb)
    print(f" 100%")

    # Validate output
    if not os.path.exists(video_path):
        raise Exception(f"Video file not found: {video_path}")

    file_size = os.path.getsize(video_path)
    print_detail("Output", f"{os.path.basename(video_path)} ({format_size(file_size)})")

    if file_size < 100_000:
        raise Exception(f"Video too small ({format_size(file_size)}), expected >100KB")

    return video_path


async def stage_3_whisper_captions(video_path: str) -> list:
    """Test caption extraction with Whisper"""
    from api.generators.caption.whisper_generator import WhisperCaptionGenerator

    generator = WhisperCaptionGenerator()
    word_timestamps = await generator.generate_captions(video_path)

    print_detail("Words", f"{len(word_timestamps)} words extracted")

    if word_timestamps:
        first = word_timestamps[0]
        sample_text = " ".join(w["text"] for w in word_timestamps[:5])
        print_detail(
            "Sample",
            f'"{sample_text}" ({first["start"]:.2f}s - {word_timestamps[min(4, len(word_timestamps)-1)]["end"]:.2f}s)'
        )

    # Validate structure
    if not isinstance(word_timestamps, list):
        raise Exception("Expected list of word timestamps")

    for w in word_timestamps:
        if not all(k in w for k in ("text", "start", "end")):
            raise Exception(f"Invalid word entry (missing keys): {w}")

    # Note: LTX-2 videos may not have speech audio, so empty captions
    # are valid. We still pass if the structure is correct.
    if not word_timestamps:
        print(f"  {Colors.YELLOW}Warning: No words found — video may lack speech audio.{Colors.RESET}")
        print(f"  {Colors.YELLOW}This is expected for LTX-2 generated videos without narration.{Colors.RESET}")

    return word_timestamps


async def stage_4_ffmpeg_overlay(
    video_path: str,
    word_timestamps: list,
    output_dir: str,
) -> str:
    """Test caption overlay with FFmpeg"""
    from api.generators.caption.ffmpeg_overlay import FFmpegCaptionOverlay

    overlay = FFmpegCaptionOverlay()
    output_path = os.path.join(output_dir, "final_captioned.mp4")

    # If no captions were extracted (no speech in video), create a dummy
    # timestamp so we can still test the FFmpeg overlay pipeline
    if not word_timestamps:
        print(f"  {Colors.YELLOW}No captions from Whisper — using dummy caption for overlay test{Colors.RESET}")
        word_timestamps = [
            {"text": "Test", "start": 0.0, "end": 1.0},
            {"text": "caption", "start": 1.0, "end": 2.0},
            {"text": "overlay", "start": 2.0, "end": 3.0},
        ]

    result_path = await overlay.overlay_captions(video_path, word_timestamps, output_path)

    # Report which encoder was used
    encoder = getattr(overlay, "last_encoder", "unknown")
    encoder_label = "h264_nvenc (GPU)" if encoder == "h264_nvenc" else "libx264 (CPU)"
    print_detail("Encoder", encoder_label)

    if encoder == "libx264":
        print(f"  {Colors.YELLOW}Note: Using CPU encoding. For GPU, install NVENC-capable FFmpeg.{Colors.RESET}")

    # Validate output
    if not os.path.exists(result_path):
        raise Exception(f"Output file not found: {result_path}")

    file_size = os.path.getsize(result_path)
    print_detail("Output", f"{os.path.basename(result_path)} ({format_size(file_size)})")

    if file_size < 100_000:
        raise Exception(f"Output too small ({format_size(file_size)}), expected >100KB")

    return result_path


def stage_5_final_validation(video_path: str) -> dict:
    """Validate the final video with ffprobe"""

    if not os.path.exists(video_path):
        raise Exception(f"Final video not found: {video_path}")

    file_size = os.path.getsize(video_path)
    if file_size == 0:
        raise Exception("Final video is 0 bytes")

    # Run ffprobe for format info
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ],
            capture_output=True, text=True, timeout=30
        )

        if proc.returncode != 0:
            raise Exception(f"ffprobe failed: {proc.stderr}")

        import json
        probe = json.loads(proc.stdout)

        # Extract info
        fmt = probe.get("format", {})
        streams = probe.get("streams", [])

        duration = float(fmt.get("duration", 0))
        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

        video_codec = video_streams[0]["codec_name"] if video_streams else "none"
        audio_codec = audio_streams[0]["codec_name"] if audio_streams else "none"

        format_label = f"MP4 ({video_codec.upper()}"
        if audio_streams:
            format_label += f" + {audio_codec.upper()}"
        format_label += ")"

        print_detail("Format", format_label)
        print_detail("Duration", f"{duration:.1f}s")
        print_detail("Size", format_size(file_size))

        if not video_streams:
            raise Exception("No video stream found in output")

        return {
            "format": format_label,
            "duration": duration,
            "size": file_size,
            "video_codec": video_codec,
            "audio_codec": audio_codec,
        }

    except FileNotFoundError:
        # ffprobe not available, do basic validation
        print_detail("Format", f"MP4 (ffprobe unavailable for details)")
        print_detail("Size", format_size(file_size))
        return {"size": file_size}


# ── Main runner ──────────────────────────────────────────────────────────────

async def run_tests(keep_artifacts: bool):
    print_header()

    # Create temp output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("generations", "videos", f"integration_test_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    results = []  # (stage_name, passed, elapsed)
    stage_data = {}  # Pass data between stages

    stages = [
        (0, "Checking prerequisites", "Prerequisites"),
        (1, "Prompt expansion (Ollama/Gemma)", "Prompt expansion"),
        (2, "Video generation (ComfyUI/LTX-2)", "Video generation"),
        (3, "Caption extraction (Whisper)", "Caption extraction"),
        (4, "Caption overlay (FFmpeg)", "Caption overlay"),
        (5, "Final validation", "Final validation"),
    ]

    for stage_num, desc, label in stages:
        print_stage(stage_num, desc)
        t0 = time.time()

        try:
            if stage_num == 0:
                stage_0_prerequisites()

            elif stage_num == 1:
                stage_data["expanded_prompt"] = await stage_1_prompt_expansion()

            elif stage_num == 2:
                stage_data["video_path"] = await stage_2_video_generation(
                    stage_data["expanded_prompt"], output_dir
                )

            elif stage_num == 3:
                stage_data["word_timestamps"] = await stage_3_whisper_captions(
                    stage_data["video_path"]
                )

            elif stage_num == 4:
                stage_data["final_video"] = await stage_4_ffmpeg_overlay(
                    stage_data["video_path"],
                    stage_data["word_timestamps"],
                    output_dir,
                )

            elif stage_num == 5:
                stage_5_final_validation(stage_data["final_video"])

            elapsed = time.time() - t0
            print_pass(label, elapsed)
            results.append((label, True, elapsed))

        except Exception as e:
            elapsed = time.time() - t0
            print_fail(label, str(e))
            results.append((label, False, elapsed))
            # Stop — later stages depend on earlier ones
            break

    # ── Summary ──────────────────────────────────────────────────────────
    total_time = sum(r[2] for r in results)
    passed = sum(1 for r in results if r[1])
    total = len(stages)

    print(f"\n{Colors.BOLD}{'=' * 48}")
    print(f"  RESULTS: {passed}/{total} PASSED  ({total_time:.1f}s total)")
    print(f"{'=' * 48}{Colors.RESET}")

    # Per-stage breakdown
    for label, ok, elapsed in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if ok else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {status}  {label:25s} {elapsed:>7.1f}s")
    print()

    # Cleanup
    if passed == total and not keep_artifacts:
        print(f"Cleaning up test artifacts in {output_dir}...")
        shutil.rmtree(output_dir, ignore_errors=True)
        print("Done.")
    elif keep_artifacts:
        print(f"Artifacts kept in: {output_dir}")
    else:
        print(f"Artifacts preserved (test failed) in: {output_dir}")

    return passed == total


def main():
    parser = argparse.ArgumentParser(description="VidiGen AI Integration Test Suite")
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep generated artifacts after successful test",
    )
    args = parser.parse_args()

    success = asyncio.run(run_tests(keep_artifacts=args.keep))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
