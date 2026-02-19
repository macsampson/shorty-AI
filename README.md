# Apparition.io

**Apparition.io** is a text-to-video generation platform. Enter a short prompt, and the pipeline produces a captioned MP4 — ready for short-form platforms like YouTube Shorts, TikTok, and Instagram Reels.

## How It Works

A 4-stage pipeline processes each request:

```
Prompt → [Ollama/Gemma 3] → [ComfyUI/LTX-2] → [Whisper] → [FFmpeg] → Captioned MP4
```

| Stage | Service | What it does |
|---|---|---|
| 1. Prompt expansion | Ollama (Gemma 3 12B) | Expands a short prompt into an ~80-word cinematic description |
| 2. Video generation | ComfyUI (LTX-2 model) | Renders the video via a 2-pass diffusion pipeline |
| 3. Caption extraction | Whisper (medium) | Extracts word-level timestamps from the video audio |
| 4. Caption overlay | FFmpeg (NVENC) | Burns green-highlighted word-karaoke captions onto the video |

## Architecture

| Service  | Port  | Purpose                               |
|----------|-------|---------------------------------------|
| Ollama   | 11434 | Prompt expansion (Gemma 3 12B)        |
| ComfyUI  | 8188  | Video generation (LTX-2 distilled FP8)|
| API      | 8000  | FastAPI orchestrator                  |
| Frontend | 3000  | React/Vite/TypeScript UI              |

All services run **natively on Windows** via PowerShell launch scripts — no Docker required.

**Single-GPU VRAM management**: The RTX 3090 loads each model sequentially. After each stage, the previous model is unloaded (`Ollama keep_alive: 0`, ComfyUI `/free`, `torch.cuda.empty_cache()`), and the pipeline polls `nvidia-smi` before loading the next one.

## Prerequisites

- **Windows** with PowerShell
- **NVIDIA GPU** with 24 GB VRAM (RTX 3090 or equivalent)
- [Conda](https://docs.conda.io/en/latest/) (for the Python API environment)
- [Node.js](https://nodejs.org/) (v18+, for the frontend)
- [Ollama](https://ollama.com/) installed and on PATH
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) installed (default path: `O:/dev/ComfyUI`)
  - LTX-2 model: `ltx-2-19b-distilled-fp8.safetensors` in ComfyUI's models directory
  - Run `scripts/download_ltx2.ps1` to download the model automatically

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/macsampson/ai-shorts.git
   cd ai-shorts
   ```

2. **Run the setup script** (creates conda env, installs dependencies):

   ```powershell
   .\scripts\setup.ps1
   ```

3. **Pull the Ollama model:**

   ```bash
   ollama pull gemma3:12b
   ```

4. **Configure environment variables** (optional — defaults work for local installs):

   Create a `.env` file in the project root:

   ```env
   COMFYUI_OUTPUT_DIR=O:/dev/ComfyUI/output
   OLLAMA_MODEL=gemma3:12b
   WHISPER_MODEL_SIZE=medium
   ```

## Running

Launch all four services at once:

```powershell
.\scripts\start-all.ps1
```

This opens each service in its own terminal window and runs smoke tests to verify connectivity. Then open [http://localhost:3000](http://localhost:3000).

To stop all services:

```powershell
.\scripts\stop-all.ps1
```

## Usage

1. Open [http://localhost:3000](http://localhost:3000)
2. Enter a prompt (e.g., `"A lone astronaut walking on Mars at sunset"`)
3. Set the duration (5–30 seconds)
4. Click **Generate**
5. Watch real-time progress via WebSocket, then view/download the finished video

Generated videos are stored in `generations/videos/` and **auto-deleted after 24 hours**.

## Development

### Backend

```bash
conda activate shorty-ai
python api/main.py                  # Start API on :8000
```

### Frontend

```bash
cd frontend
npm run dev                         # Vite dev server on :3000
npm run build                       # Production build → frontend/build/
```

### Tests

```bash
# Unit tests (mocked — no services required)
python -m pytest tests/ --ignore=tests/smoke -v --tb=short

# With coverage (target: 60%)
python -m pytest tests/ --ignore=tests/smoke --cov --cov-report=term-missing

# Smoke tests (require all 4 services running)
python -m pytest tests/smoke/ -m smoke -v --tb=short

# Full integration test (runs actual pipeline end-to-end)
python scripts/test-integration.py
```

Or use the PowerShell wrapper:

```powershell
.\scripts\run-tests.ps1             # Unit tests
.\scripts\run-tests.ps1 -Smoke      # Smoke tests
.\scripts\run-tests.ps1 -Coverage   # With coverage
.\scripts\run-tests.ps1 -All        # Everything
```

## Configuration

All config lives in `api/config.py` via Pydantic `BaseSettings`, overridable via `.env`.

| Setting | Default | Description |
|---|---|---|
| `ollama_base_url` | `http://localhost:11434` | Ollama endpoint |
| `ollama_model` | `gemma3:12b` | LLM for prompt expansion |
| `comfyui_base_url` | `http://localhost:8188` | ComfyUI endpoint |
| `comfyui_output_dir` | `O:/dev/ComfyUI/output` | Where ComfyUI writes videos |
| `whisper_model_size` | `medium` | Whisper model (base/small/medium/large) |
| `vidigen_frame_count` | `121` | Default frames (~5s at 24fps) |
| `single_gpu_mode` | `true` | Sequential model loading |

### LTX-2 Constraints

- **Frame count** must be `8n + 1` (e.g. 97, 121, 161, 241, 721). Formula: `frames = (seconds × 24 // 8) × 8 + 1`. Both `main.py` and `comfyui_generator.py` enforce this automatically.
- **Width/height** must be `32n + 1` (e.g. 321, 641, 961). Set in `comfyui_workflows/video_ltx2_t2v_distilled_api.json`.

## Project Structure

```
api/
  main.py                    # FastAPI app + pipeline orchestrator
  config.py                  # Pydantic settings
  generators/
    factory.py               # Wires up generator implementations
    prompt/ollama_expander.py
    video/comfyui_generator.py
    caption/whisper_generator.py
    caption/ffmpeg_overlay.py
  vram_monitor.py            # flush_vram / wait_for_vram
  websocket_manager.py       # Real-time progress via WebSocket
  cleanup_scheduler.py       # 24-hour auto-delete
comfyui_workflows/
  video_ltx2_t2v_distilled_api.json
frontend/src/
  components/                # VideoForm, VideoLibrary, VideoDetails, etc.
scripts/
  start-all.ps1 / stop-all.ps1
  setup.ps1
  test-integration.py
tests/                       # pytest unit + smoke tests
```

## License

MIT License
