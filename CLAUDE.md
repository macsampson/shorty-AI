# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

Apparition.io is a text-to-video generation platform. A user enters a short prompt, which flows through a 4-stage pipeline: prompt expansion → video generation → caption extraction → caption overlay, producing a captioned MP4.

**Runtime services** (all on one Windows machine with a single RTX 3090):

| Service  | Port  | Purpose                        |
| -------- | ----- | ------------------------------ |
| Ollama   | 11434 | Prompt expansion (Gemma 3 12B) |
| ComfyUI  | 8188  | Video generation (LTX-2)       |
| API      | 8000  | FastAPI orchestrator           |
| Frontend | 3000  | React/Vite/TS UI               |

Services are launched natively via PowerShell scripts (`scripts/start-all.ps1`), not Docker. The API runs in a conda environment named `shorty-ai`.

**Pipeline flow** (`api/main.py` → `run_vidigen_pipeline`):

1. **Prompt expansion** — `OllamaPromptExpander` expands a short prompt into an ~80-word cinematic description
2. **Video generation** — `ComfyUIVideoGenerator` sends the expanded prompt to ComfyUI running the LTX-2 workflow, receives video via WebSocket
3. **Caption extraction** — `WhisperCaptionGenerator` extracts word-level timestamps from the video's audio
4. **Caption overlay** — `FFmpegCaptionOverlay` groups words into 5-word phrases, generates ASS subtitles with green word-level highlighting, burns them in with FFmpeg (NVENC GPU encoding, falls back to libx264 CPU)

**VRAM management** (single RTX 3090, sequential model loading):
1. Ollama generates prompt → `keep_alive: 0` unloads model immediately
2. ComfyUI loads LTX-2 → renders video → `POST /free` endpoint unloads model
3. Whisper loads (lazy-loaded) → transcribes → `torch.cuda.empty_cache()` frees VRAM
4. FFmpeg encodes with NVENC (minimal VRAM)

Between stages, `flush_vram()` performs all three unload steps, then `wait_for_vram()` polls nvidia-smi until enough free memory is available.

**Generator pattern**: Abstract base classes in `api/generators/base.py` (`PromptExpansionGenerator`, `VideoGenerator`, `CaptionGenerator`). Concrete implementations live in `api/generators/{prompt,video,caption}/`. `GeneratorFactory` in `api/generators/factory.py` wires them together.

**Frontend**: Single-page React app with `VideoForm` (prompt input + duration slider + progress bar), `VideoLibrary` (paginated grid of past generations), and `VideoDetails` (video player + metadata). Vite proxies `/api` and `/generations` to the API at localhost:8000.

**WebSocket progress**: The frontend connects to `ws://localhost:8000/ws/video_generation/{job_id}` to receive real-time progress updates from the pipeline via `ConnectionManager` (`api/websocket_manager.py`).

## Commands

```bash
# Backend
conda activate shorty-ai
python api/main.py                    # Start API server on :8000

# Frontend
cd frontend && npm run dev            # Vite dev server on :3000
cd frontend && npm run build          # Production build → frontend/build/

# Unit tests (mocked, no services needed)
python -m pytest tests/ --ignore=tests/smoke -v --tb=short
python -m pytest tests/test_main.py -v          # Single test file
python -m pytest tests/test_main.py::test_name   # Single test

# Unit tests with coverage
python -m pytest tests/ --ignore=tests/smoke --cov --cov-report=term-missing

# Smoke tests (require all 4 services running)
python -m pytest tests/smoke/ -m smoke -v --tb=short

# Full integration test (requires services, runs actual pipeline)
python scripts/test-integration.py [--keep]

# Start/stop all services
.\scripts\start-all.ps1
.\scripts\stop-all.ps1

# PowerShell test runner (convenience wrapper)
.\scripts\run-tests.ps1              # Unit tests
.\scripts\run-tests.ps1 -Smoke       # Smoke tests
.\scripts\run-tests.ps1 -Coverage    # With coverage
.\scripts\run-tests.ps1 -All         # Everything
```

## LTX-2 Video Generation Details

- **Model**: `ltx-2-19b-distilled-fp8.safetensors`
- **Workflow**: `comfyui_workflows/video_ltx2_t2v_distilled_api.json` (API format — flat dict of `node_id → {class_type, inputs}`, not UI format with nodes/links)
- **2-pass pipeline**: 8 diffusion steps → latent upsampling (`LTXVLatentUpsampler`) → 3 refinement steps → separate audio/video VAE decode → `CreateVideo` → `SaveVideo`
- **ComfyUI API interaction**: POST workflow to `http://localhost:8188/prompt` with `client_id`, monitor progress via `ws://localhost:8188/ws?clientId={id}`, copy output from `comfyui_output_dir`
- **Frame count** must be `8n + 1` (e.g., 97, 121, 161, 241, 721). Formula: `frames = (seconds * 24 // 8) * 8 + 1`. Default: 121 (~5s at 24fps). Enforced in both `main.py` and `comfyui_generator.py`.
- **Width/height** must be `32n + 1` (e.g., 321, 641, 961). Set in the workflow JSON.
- **Duration slider**: Frontend allows 5-30s; `duration_seconds` on `GenerateTextRequest` has `ge=5, le=30` validation.
- LTX-2 videos may lack speech audio — empty captions from Whisper are valid and handled gracefully (overlay step is skipped).

## Testing

- pytest with `asyncio_mode = "auto"` (pyproject.toml). Tests use `pytest-asyncio`.
- `tests/conftest.py` has an `autouse` fixture that overrides all settings to point at fake service URLs — unit tests never hit real Ollama/ComfyUI/Whisper.
- Markers: `smoke` (service connectivity), `slow`, `gpu`.
- Coverage target: 60% (`fail_under = 60` in pyproject.toml), source = `api/`.
- Dev test dependencies: `requirements-dev.txt` (pytest, pytest-asyncio, pytest-cov, httpx, aioresponses).

## Configuration

All config is in `api/config.py` via Pydantic `BaseSettings`, loaded from `.env`. Key settings: `ollama_base_url`, `ollama_model`, `comfyui_base_url`, `comfyui_output_dir` (points to local ComfyUI install at `O:/dev/ComfyUI/output`), `whisper_model_size`, `vidigen_frame_count`, `single_gpu_mode`.

## Cleanup & Retention

Generated videos in `generations/videos/` are auto-deleted after 24 hours by `CleanupScheduler`, an asyncio background task started on FastAPI startup.

## Code Style

- **Python**: PEP 8, type hints, Pydantic models for validation.
- **TypeScript/React**: Functional components with hooks. Tailwind CSS v4 (via `@tailwindcss/vite` plugin).
