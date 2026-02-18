from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import os
import json
import datetime
import uuid
import asyncio
import logging

logger = logging.getLogger(__name__)

from urllib.parse import unquote
from pathlib import Path
from api.generators.factory import GeneratorFactory
from api.models import GenerateTextRequest, VideoGenerationStatus
from api.websocket_manager import manager
from api.generators.caption.ffmpeg_overlay import FFmpegCaptionOverlay
from api.vram_monitor import flush_vram, wait_for_vram, get_vram_usage
from api.cleanup_scheduler import CleanupScheduler

# Import the settings from config
from api.config import settings

app = FastAPI()

# Define the path for generated assets (relative to project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATIONS_DIR = os.environ.get("GENERATIONS_DIR", os.path.join(PROJECT_ROOT, "generations"))
GENERATED_VIDEOS_DIR = os.path.join(GENERATIONS_DIR, "videos")


@app.on_event("startup")
async def startup_event():
    os.makedirs(GENERATED_VIDEOS_DIR, exist_ok=True)

    # Start 24-hour cleanup scheduler
    cleanup_scheduler = CleanupScheduler(
        videos_dir=Path(GENERATED_VIDEOS_DIR),
        retention_hours=24
    )
    asyncio.create_task(cleanup_scheduler.start())


# Mount the generated directories
def mount_directories():
    os.makedirs(GENERATIONS_DIR, exist_ok=True)
    app.mount("/generations", StaticFiles(directory=GENERATIONS_DIR), name="generations")

mount_directories()


# ------------ WEBSOCKET ENDPOINT ------------
@app.websocket("/ws/video_generation/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time generation progress"""
    await manager.connect(job_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)


# ------------ VIDIGEN AI PIPELINE ------------
@app.post("/generate_video_vidigen")
async def generate_video_vidigen(
    request: GenerateTextRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate video using VidiGen AI pipeline:
    1. Prompt expansion (Ollama/Gemma)
    2. Video generation (ComfyUI/LTX-2)
    3. Caption extraction (Whisper)
    4. Caption overlay (FFmpeg)
    """

    job_id = str(uuid.uuid4())

    # Run pipeline in background
    background_tasks.add_task(
        run_vidigen_pipeline,
        job_id,
        request.prompt,
        request.duration_seconds
    )

    return {
        "job_id": job_id,
        "status": "started",
        "pipeline": "vidigen"
    }

async def run_vidigen_pipeline(job_id: str, prompt: str, duration_seconds: int = 5):
    """Execute the VidiGen AI pipeline with progress tracking"""

    try:
        # Create output directory
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(GENERATED_VIDEOS_DIR) / f"{timestamp}_{job_id}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Flush VRAM from any previous runs
        await flush_vram()
        await wait_for_vram(min_free_gb=12, timeout=30)

        # Stage 1: Video Generation (0-80%)
        await manager.send_progress(job_id, 0, "generation", "Starting LTX-2 video generation...")

        video_generator = GeneratorFactory.get_video_generator()

        # Create progress callback to forward ComfyUI progress
        async def comfyui_progress_callback(progress_pct: float):
            # Map ComfyUI 0-100% to overall 0-80%
            overall_progress = progress_pct * 0.8
            await manager.send_progress(
                job_id,
                overall_progress,
                "generation",
                f"Generating video: {progress_pct:.0f}% complete"
            )

        # LTX-2 requires frame count = 8n + 1 (e.g. 121, 241, 721)
        raw_frames = duration_seconds * 24
        frame_count = (raw_frames // 8) * 8 + 1
        video_path = await video_generator.generate_video(
            prompt,
            str(output_dir),
            comfyui_progress_callback,
            frame_count=frame_count
        )

        await manager.send_progress(job_id, 80, "generation", "Video generated successfully")

        # Flush VRAM after ComfyUI/LTX-2
        await flush_vram()
        await wait_for_vram(min_free_gb=5, timeout=30)

        # Stage 3: Caption Generation (80-90%)
        await manager.send_progress(job_id, 80, "captions", "Extracting captions with Whisper...")

        caption_generator = GeneratorFactory.get_caption_generator()
        word_timestamps = await caption_generator.generate_captions(video_path)

        # Log Whisper output for debugging
        logger.info(f"[Whisper] Extracted {len(word_timestamps)} words from {video_path}")
        if word_timestamps:
            for i, w in enumerate(word_timestamps[:10]):
                logger.info(f"[Whisper]   [{i}] {w['start']:.2f}s-{w['end']:.2f}s: '{w['text']}'")
            if len(word_timestamps) > 10:
                logger.info(f"[Whisper]   ... and {len(word_timestamps) - 10} more words")
        else:
            logger.warning("[Whisper] No words extracted — video may have no audio/speech")

        # Save Whisper output for debugging
        whisper_debug_path = output_dir / "whisper_output.json"
        with open(whisper_debug_path, "w") as f:
            json.dump(word_timestamps, f, indent=2)
        logger.info(f"[Whisper] Debug output saved to {whisper_debug_path}")

        await manager.send_progress(
            job_id,
            90,
            "captions",
            f"Extracted {len(word_timestamps)} words"
        )

        # Stage 4: Caption Overlay (90-100%)
        if not word_timestamps:
            logger.warning("[Pipeline] Skipping caption overlay — no words to overlay")
            final_video_path = video_path
        else:
            await manager.send_progress(job_id, 90, "overlay", "Overlaying captions on video...")

            ffmpeg_overlay = FFmpegCaptionOverlay()
            final_video_path = str(output_dir / f"final_{job_id}.mp4")

            final_video_path = await ffmpeg_overlay.overlay_captions(
                video_path,
                word_timestamps,
                final_video_path
            )

        # Save metadata
        metadata = {
            "job_id": job_id,
            "prompt": prompt,
            "duration_seconds": duration_seconds,
            "video_path": final_video_path,
            "word_count": len(word_timestamps),
            "created_at": datetime.datetime.now().isoformat()
        }

        with open(output_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        # Complete
        await manager.send_progress(job_id, 100, "complete", "Video ready!")

    except Exception as e:
        # Error handling
        await manager.send_progress(job_id, -1, "error", str(e))
        raise


# ------------ PROMPT EXPANSION (TEST) ------------
@app.post("/expand_prompt")
async def expand_prompt(request: GenerateTextRequest):
    """Expand a simple prompt using Ollama/Gemma — no video generation"""
    try:
        expander = GeneratorFactory.get_prompt_expander()
        expanded = await expander.expand_prompt(request.prompt)
        return {"original": request.prompt, "expanded": expanded}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------ VRAM MONITORING ------------
@app.get("/vram_status")
async def get_vram_status():
    """Get current VRAM usage"""
    return get_vram_usage()


# ------------ CONTENT BROWSING ------------
@app.get("/get_generated_content/{folder_name:path}")
async def get_generated_content(folder_name: str):
    decoded_folder_name = unquote(folder_name)

    folder_path = os.path.join(GENERATED_VIDEOS_DIR, decoded_folder_name)
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_path}")

    # Load metadata if available
    metadata_path = os.path.join(folder_path, "metadata.json")
    script_path = os.path.join(folder_path, "script.json")

    script_data = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            script_data = json.load(f)
    elif os.path.exists(script_path):
        with open(script_path, "r") as f:
            script_data = json.load(f)

    # Check for videos in the main folder
    video_files = []
    video_urls = []

    main_folder_videos = [f for f in os.listdir(folder_path) if f.endswith('.mp4')]
    for video in main_folder_videos:
        video_files.append(video)
        video_urls.append(f"/generations/videos/{folder_name}/{video}")

    # Check 'videos' subfolder if it exists
    videos_subfolder = os.path.join(folder_path, "videos")
    if os.path.exists(videos_subfolder) and os.path.isdir(videos_subfolder):
        subfolder_videos = [f for f in os.listdir(videos_subfolder) if f.endswith('.mp4')]
        for video in subfolder_videos:
            video_files.append(os.path.join("videos", video))
            video_urls.append(f"/generations/videos/{folder_name}/videos/{video}")

    if not video_files:
        raise HTTPException(status_code=404, detail=f"No video files found in folder: {folder_path}")

    return {
        "script": script_data,
        "image_urls": [],
        "video_urls": video_urls,
        "image_files": [],
        "video_files": video_files
    }

@app.get("/list_generated_content")
async def list_generated_content():
    folders = [f for f in os.listdir(GENERATED_VIDEOS_DIR) if os.path.isdir(os.path.join(GENERATED_VIDEOS_DIR, f))]
    return {"folders": folders}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    uvicorn.run(app, host="0.0.0.0", port=8000)
