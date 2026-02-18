import asyncio
import subprocess
import time
from typing import Dict

import aiohttp
from api.config import settings


def get_vram_usage() -> Dict[str, float]:
    """Get current system-wide VRAM usage via nvidia-smi"""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return {"allocated_gb": 0, "reserved_gb": 0, "total_gb": 0, "free_gb": 0}

        line = result.stdout.strip().split("\n")[0]
        used_mb, total_mb = [float(x.strip()) for x in line.split(",")]

        total_gb = round(total_mb / 1024, 2)
        used_gb = round(used_mb / 1024, 2)
        free_gb = round(total_gb - used_gb, 2)

        return {
            "allocated_gb": used_gb,
            "reserved_gb": used_gb,
            "total_gb": total_gb,
            "free_gb": free_gb,
        }
    except Exception:
        return {"allocated_gb": 0, "reserved_gb": 0, "total_gb": 0, "free_gb": 0}


async def flush_vram() -> None:
    """Actively unload models from Ollama, ComfyUI, and torch to free VRAM"""

    # Unload Ollama models
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            # List loaded models
            async with session.get(f"{settings.ollama_base_url}/api/ps") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for model in data.get("models", []):
                        model_name = model.get("name", "")
                        if model_name:
                            await session.post(
                                f"{settings.ollama_base_url}/api/generate",
                                json={"model": model_name, "keep_alive": 0},
                            )
                            print(f"[VRAM] Unloaded Ollama model: {model_name}")
    except Exception as e:
        print(f"[VRAM] Ollama unload skipped: {e}")

    # Unload ComfyUI models
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(
                f"{settings.comfyui_base_url}/free",
                json={"unload_models": True, "free_memory": True},
            ) as resp:
                if resp.status == 200:
                    print("[VRAM] Unloaded ComfyUI models")
    except Exception as e:
        print(f"[VRAM] ComfyUI unload skipped: {e}")

    # Clear PyTorch CUDA cache
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            print("[VRAM] Cleared PyTorch CUDA cache")
    except Exception as e:
        print(f"[VRAM] PyTorch cache clear skipped: {e}")

    # Brief pause for GPU memory to settle
    await asyncio.sleep(2)


async def wait_for_vram(min_free_gb: float, timeout: int = 60) -> bool:
    """
    Wait until specified amount of VRAM is available (system-wide)

    Args:
        min_free_gb: Minimum GB of free VRAM required
        timeout: Maximum seconds to wait

    Returns:
        True if VRAM available, False if timeout
    """
    start = time.time()

    while time.time() - start < timeout:
        stats = get_vram_usage()
        free = stats["free_gb"]
        if free >= min_free_gb:
            return True
        print(f"Waiting for VRAM: {free:.1f}GB free, need {min_free_gb:.1f}GB...")
        await asyncio.sleep(2)

    print(f"VRAM wait timed out after {timeout}s")
    return False
