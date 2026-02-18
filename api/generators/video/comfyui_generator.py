import aiohttp
import asyncio
import json
import random
import shutil
import uuid
import os
from typing import Optional, Callable
from api.generators.base import VideoGenerator
from api.config import settings


class ComfyUIVideoGenerator(VideoGenerator):
    def __init__(self):
        self.base_url = settings.comfyui_base_url
        self.workflow_template_path = "comfyui_workflows/video_ltx2_t2v_distilled_api.json"

    def _load_workflow_template(self) -> dict:
        """Load and return the ComfyUI workflow JSON template"""
        with open(self.workflow_template_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _inject_prompt(self, workflow: dict, prompt: str) -> dict:
        """Inject the expanded prompt into the workflow's PrimitiveStringMultiline node"""
        for node_id, node in workflow.items():
            if node.get("class_type") == "PrimitiveStringMultiline":
                node["inputs"]["value"] = prompt
                break
        return workflow

    def _configure_workflow(self, workflow: dict, frame_count: Optional[int] = None) -> dict:
        """Configure workflow settings: frame count, seed, resolution"""
        seed1 = random.randint(0, 2**32 - 1)
        seed2 = random.randint(0, 2**32 - 1)

        raw = frame_count if frame_count is not None else getattr(settings, "vidigen_frame_count", 97)
        # LTX-2 requires frame count = 8n + 1; snap to nearest valid value
        effective_frame_count = ((raw - 1) // 8) * 8 + 1

        for node_id, node in workflow.items():
            class_type = node.get("class_type")

            if class_type == "PrimitiveInt" and node.get("_meta", {}).get("title") == "Frame Count":
                node["inputs"]["value"] = effective_frame_count

            elif class_type == "RandomNoise":
                if node["inputs"].get("noise_seed") == 5:
                    node["inputs"]["noise_seed"] = seed1
                else:
                    node["inputs"]["noise_seed"] = seed2

        return workflow

    async def generate_video(
        self,
        prompt: str,
        output_dir: str,
        progress_callback: Optional[Callable[[float], None]] = None,
        frame_count: Optional[int] = None
    ) -> str:
        """Generate video using ComfyUI with LTX-2"""

        workflow = self._load_workflow_template()
        workflow = self._inject_prompt(workflow, prompt)
        workflow = self._configure_workflow(workflow, frame_count=frame_count)

        client_id = str(uuid.uuid4())

        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Submit prompt to ComfyUI
            prompt_payload = {
                "prompt": workflow,
                "client_id": client_id
            }

            async with session.post(
                f"{self.base_url}/prompt",
                json=prompt_payload
            ) as response:
                if response.status != 200:
                    error_body = await response.text()
                    raise Exception(
                        f"ComfyUI prompt submission failed ({response.status}): {error_body}"
                    )
                result = await response.json()
                prompt_id = result["prompt_id"]
                print(f"[ComfyUI] Prompt submitted: {prompt_id}")

        # Monitor via polling (robust) + optional WebSocket progress
        video_path = await self._poll_for_completion(
            prompt_id,
            client_id,
            output_dir,
            progress_callback
        )

        if settings.single_gpu_mode:
            await self._unload_model()

        return video_path

    async def _poll_for_completion(
        self,
        prompt_id: str,
        client_id: str,
        output_dir: str,
        progress_callback: Optional[Callable[[float], None]],
        poll_interval: float = 3.0,
        max_wait: int = 900,  # 15 minutes max
    ) -> str:
        """
        Poll ComfyUI for completion. Runs a WebSocket listener in parallel
        for real-time progress updates, but uses HTTP polling as the
        primary mechanism to detect completion.
        """

        # Start WebSocket progress listener in background (best-effort)
        ws_task = asyncio.create_task(
            self._ws_progress_listener(client_id, prompt_id, progress_callback)
        )

        try:
            elapsed = 0
            timeout = aiohttp.ClientTimeout(total=15)

            while elapsed < max_wait:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                async with aiohttp.ClientSession(timeout=timeout) as session:
                    # Check if prompt is still in the queue
                    queue_status = await self._check_queue(session, prompt_id)

                    if queue_status == "running":
                        if elapsed % 30 < poll_interval:
                            print(f"[ComfyUI] Still generating... ({int(elapsed)}s elapsed)")
                        continue

                    if queue_status == "pending":
                        if elapsed % 30 < poll_interval:
                            print(f"[ComfyUI] Queued, waiting... ({int(elapsed)}s elapsed)")
                        continue

                    # Not in queue — check history for results
                    result = await self._get_output_from_history(
                        session, prompt_id, output_dir
                    )
                    if result:
                        print(f"[ComfyUI] Generation complete: {result}")
                        return result

                    # Not in queue and not in history — might have just finished,
                    # give it one more cycle
                    if queue_status == "not_found":
                        # Double-check after a short wait
                        await asyncio.sleep(2)
                        async with aiohttp.ClientSession(timeout=timeout) as session2:
                            result = await self._get_output_from_history(
                                session2, prompt_id, output_dir
                            )
                            if result:
                                print(f"[ComfyUI] Generation complete: {result}")
                                return result

                        # If still nothing, it may have errored silently
                        raise Exception(
                            "ComfyUI prompt disappeared from queue with no output. "
                            "Check ComfyUI logs for errors."
                        )

            raise Exception(f"Video generation timed out after {max_wait}s")

        finally:
            ws_task.cancel()
            try:
                await ws_task
            except (asyncio.CancelledError, Exception):
                pass

    async def _check_queue(
        self, session: aiohttp.ClientSession, prompt_id: str
    ) -> str:
        """
        Check ComfyUI queue for our prompt.
        Returns: 'running', 'pending', or 'not_found'
        """
        try:
            async with session.get(f"{self.base_url}/queue") as resp:
                if resp.status != 200:
                    return "running"  # Assume still running if we can't check
                queue = await resp.json()

            # Check running queue
            for item in queue.get("queue_running", []):
                if len(item) >= 2 and item[1] == prompt_id:
                    return "running"

            # Check pending queue
            for item in queue.get("queue_pending", []):
                if len(item) >= 2 and item[1] == prompt_id:
                    return "pending"

            return "not_found"
        except Exception as e:
            print(f"[ComfyUI] Queue check error: {e}")
            return "running"  # Assume still running on error

    async def _ws_progress_listener(
        self,
        client_id: str,
        prompt_id: str,
        progress_callback: Optional[Callable[[float], None]]
    ):
        """
        Best-effort WebSocket listener for real-time progress updates.
        This runs in the background — if it disconnects, polling still works.
        """
        ws_url = f"ws://{self.base_url.replace('http://', '')}/ws?clientId={client_id}"

        try:
            timeout = aiohttp.ClientTimeout(total=900, sock_read=900)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.ws_connect(
                    ws_url, heartbeat=30, receive_timeout=900
                ) as ws:
                    print(f"[ComfyUI WS] Connected for progress tracking")
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            msg_type = data.get("type")
                            event_data = data.get("data")

                            if not isinstance(event_data, dict):
                                continue

                            if msg_type == "progress" and progress_callback:
                                current = event_data.get("value", 0)
                                maximum = event_data.get("max", 1)
                                pct = (current / maximum) * 100
                                await progress_callback(pct)

                            elif msg_type == "executing":
                                node = event_data.get("node")
                                if node:
                                    print(f"[ComfyUI WS] Executing node: {node}")

                        elif msg.type in (
                            aiohttp.WSMsgType.ERROR,
                            aiohttp.WSMsgType.CLOSE,
                            aiohttp.WSMsgType.CLOSING,
                            aiohttp.WSMsgType.CLOSED,
                        ):
                            break
        except asyncio.CancelledError:
            pass  # Normal — cancelled when polling detects completion
        except Exception as e:
            print(f"[ComfyUI WS] Progress listener error (non-fatal): {e}")

    async def _get_output_from_history(
        self,
        session: aiohttp.ClientSession,
        prompt_id: str,
        output_dir: str
    ) -> Optional[str]:
        """Fetch output from ComfyUI history API"""
        try:
            async with session.get(f"{self.base_url}/history/{prompt_id}") as resp:
                if resp.status != 200:
                    return None
                history = await resp.json()

            prompt_history = history.get(prompt_id)
            if not prompt_history:
                return None

            # Check if there was an error in the status
            status = prompt_history.get("status", {})
            if status.get("status_str") == "error":
                messages = status.get("messages", [])
                error_msg = str(messages) if messages else "Unknown error"
                raise Exception(f"ComfyUI execution failed: {error_msg}")

            outputs = prompt_history.get("outputs", {})
            for node_id, node_output in outputs.items():
                for key in ("videos", "gifs", "images"):
                    items = node_output.get(key)
                    if items:
                        file_info = items[0]
                        output_filename = file_info["filename"]
                        subfolder = file_info.get("subfolder", "")

                        source_path = os.path.join(
                            settings.comfyui_output_dir,
                            subfolder,
                            output_filename,
                        )
                        dest_path = os.path.join(
                            output_dir, f"video_{prompt_id}.mp4"
                        )

                        shutil.copy2(source_path, dest_path)
                        return dest_path
        except Exception as e:
            if "execution failed" in str(e):
                raise
            print(f"[ComfyUI] History check error: {e}")

        return None

    async def _unload_model(self):
        """Unload LTX-2 model from VRAM"""
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(
                    f"{self.base_url}/free",
                    json={"unload_models": True, "free_memory": True}
                )
                await asyncio.sleep(2)
            except:
                pass
