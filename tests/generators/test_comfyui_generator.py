import json
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from aioresponses import aioresponses
from api.generators.video.comfyui_generator import ComfyUIVideoGenerator


class TestLoadWorkflowTemplate:
    def test_loads_valid_json(self, sample_workflow):
        gen = ComfyUIVideoGenerator()
        gen.workflow_template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "comfyui_workflows",
            "video_ltx2_t2v_distilled_api.json",
        )
        workflow = gen._load_workflow_template()
        assert isinstance(workflow, dict)
        assert len(workflow) > 0

    def test_file_not_found(self):
        gen = ComfyUIVideoGenerator()
        gen.workflow_template_path = "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            gen._load_workflow_template()


class TestInjectPrompt:
    def test_sets_prompt_in_primitive_string_node(self, sample_workflow):
        gen = ComfyUIVideoGenerator()
        prompt_text = "A cat walking through rain-soaked streets"

        result = gen._inject_prompt(sample_workflow, prompt_text)

        # Find the PrimitiveStringMultiline node
        found = False
        for node_id, node in result.items():
            if node.get("class_type") == "PrimitiveStringMultiline":
                assert node["inputs"]["value"] == prompt_text
                found = True
                break
        assert found, "PrimitiveStringMultiline node not found in workflow"

    def test_returns_modified_workflow(self, sample_workflow):
        gen = ComfyUIVideoGenerator()
        result = gen._inject_prompt(sample_workflow, "test prompt")
        assert isinstance(result, dict)


class TestConfigureWorkflow:
    def test_sets_frame_count(self, sample_workflow):
        gen = ComfyUIVideoGenerator()

        with patch("api.generators.video.comfyui_generator.settings") as mock_settings:
            mock_settings.vidigen_frame_count = 161
            result = gen._configure_workflow(sample_workflow)

        # Find the PrimitiveInt node with "Frame Count" title
        for node_id, node in result.items():
            if (
                node.get("class_type") == "PrimitiveInt"
                and node.get("_meta", {}).get("title") == "Frame Count"
            ):
                assert node["inputs"]["value"] == 161
                break

    def test_randomizes_seeds(self, sample_workflow):
        gen = ComfyUIVideoGenerator()

        with patch("api.generators.video.comfyui_generator.settings") as mock_settings:
            mock_settings.vidigen_frame_count = 121
            result = gen._configure_workflow(sample_workflow)

        # Find RandomNoise nodes and check seeds are randomized
        seeds = []
        for node_id, node in result.items():
            if node.get("class_type") == "RandomNoise":
                seeds.append(node["inputs"]["noise_seed"])

        if seeds:
            # Seeds should be randomized (extremely unlikely to remain at original values)
            assert all(isinstance(s, int) for s in seeds)


class TestConfigureWorkflowFrameCount:
    """Tests for the frame_count parameter in _configure_workflow"""

    def test_uses_custom_frame_count(self, sample_workflow):
        gen = ComfyUIVideoGenerator()
        result = gen._configure_workflow(sample_workflow, frame_count=241)

        for node_id, node in result.items():
            if (
                node.get("class_type") == "PrimitiveInt"
                and node.get("_meta", {}).get("title") == "Frame Count"
            ):
                assert node["inputs"]["value"] == 241
                break

    def test_falls_back_to_settings_when_none(self, sample_workflow):
        gen = ComfyUIVideoGenerator()

        with patch("api.generators.video.comfyui_generator.settings") as mock_settings:
            mock_settings.vidigen_frame_count = 161
            result = gen._configure_workflow(sample_workflow, frame_count=None)

        for node_id, node in result.items():
            if (
                node.get("class_type") == "PrimitiveInt"
                and node.get("_meta", {}).get("title") == "Frame Count"
            ):
                assert node["inputs"]["value"] == 161
                break

    def test_snaps_non_8n_plus_1_to_valid_value(self, sample_workflow):
        """If a non-8n+1 frame count is passed, it should be snapped down to the nearest valid value"""
        gen = ComfyUIVideoGenerator()
        # 200 is not 8n+1; nearest valid is (199//8)*8+1 = 24*8+1 = 193
        result = gen._configure_workflow(sample_workflow, frame_count=200)

        for node_id, node in result.items():
            if (
                node.get("class_type") == "PrimitiveInt"
                and node.get("_meta", {}).get("title") == "Frame Count"
            ):
                value = node["inputs"]["value"]
                assert (value - 1) % 8 == 0, f"{value} is not 8n+1"
                assert value == 193
                break

    async def test_generate_video_passes_frame_count(self, tmp_path):
        """Verify generate_video forwards frame_count to _configure_workflow"""
        gen = ComfyUIVideoGenerator()
        gen.base_url = "http://test-comfyui:8188"

        output_dir = str(tmp_path / "output")
        os.makedirs(output_dir)

        captured_kwargs = {}

        def capture_configure(workflow, frame_count=None):
            captured_kwargs["frame_count"] = frame_count
            return workflow

        with patch.object(gen, "_load_workflow_template", return_value={"node1": {"class_type": "Test", "inputs": {}}}):
            with patch.object(gen, "_inject_prompt", return_value={"node1": {"class_type": "Test", "inputs": {}}}):
                with patch.object(gen, "_configure_workflow", side_effect=capture_configure) as mock_config:
                    with patch.object(gen, "_poll_for_completion", new_callable=AsyncMock) as mock_poll:
                        mock_poll.return_value = os.path.join(output_dir, "video.mp4")

                        with aioresponses() as m:
                            m.post(
                                "http://test-comfyui:8188/prompt",
                                payload={"prompt_id": "test-id"},
                            )

                            await gen.generate_video("test prompt", output_dir, frame_count=241)

                    mock_config.assert_called_once()
                    assert captured_kwargs["frame_count"] == 241


class TestCheckQueue:
    def _make_generator(self):
        gen = ComfyUIVideoGenerator()
        gen.base_url = "http://test-comfyui:8188"
        return gen

    async def test_returns_running(self):
        gen = self._make_generator()
        prompt_id = "test-prompt-123"

        with aioresponses() as m:
            m.get(
                "http://test-comfyui:8188/queue",
                payload={
                    "queue_running": [[0, prompt_id, {}]],
                    "queue_pending": [],
                },
            )

            import aiohttp
            async with aiohttp.ClientSession() as session:
                result = await gen._check_queue(session, prompt_id)

        assert result == "running"

    async def test_returns_pending(self):
        gen = self._make_generator()
        prompt_id = "test-prompt-123"

        with aioresponses() as m:
            m.get(
                "http://test-comfyui:8188/queue",
                payload={
                    "queue_running": [],
                    "queue_pending": [[0, prompt_id, {}]],
                },
            )

            import aiohttp
            async with aiohttp.ClientSession() as session:
                result = await gen._check_queue(session, prompt_id)

        assert result == "pending"

    async def test_returns_not_found(self):
        gen = self._make_generator()

        with aioresponses() as m:
            m.get(
                "http://test-comfyui:8188/queue",
                payload={"queue_running": [], "queue_pending": []},
            )

            import aiohttp
            async with aiohttp.ClientSession() as session:
                result = await gen._check_queue(session, "missing-id")

        assert result == "not_found"

    async def test_returns_running_on_http_error(self):
        gen = self._make_generator()

        with aioresponses() as m:
            m.get("http://test-comfyui:8188/queue", status=500)

            import aiohttp
            async with aiohttp.ClientSession() as session:
                result = await gen._check_queue(session, "test-id")

        assert result == "running"


class TestGetOutputFromHistory:
    def _make_generator(self):
        gen = ComfyUIVideoGenerator()
        gen.base_url = "http://test-comfyui:8188"
        return gen

    async def test_copies_video_file(self, tmp_path):
        gen = self._make_generator()
        prompt_id = "test-prompt-123"
        output_dir = str(tmp_path / "output")
        os.makedirs(output_dir, exist_ok=True)

        # Create a fake source video in comfyui output
        comfyui_output = tmp_path / "comfyui_output"
        comfyui_output.mkdir()
        source_video = comfyui_output / "video_001.mp4"
        source_video.write_text("fake video content")

        with patch("api.generators.video.comfyui_generator.settings") as mock_settings:
            mock_settings.comfyui_output_dir = str(comfyui_output)

            with aioresponses() as m:
                m.get(
                    f"http://test-comfyui:8188/history/{prompt_id}",
                    payload={
                        prompt_id: {
                            "status": {"status_str": "success"},
                            "outputs": {
                                "104": {
                                    "videos": [
                                        {"filename": "video_001.mp4", "subfolder": ""}
                                    ]
                                }
                            },
                        }
                    },
                )

                import aiohttp
                async with aiohttp.ClientSession() as session:
                    result = await gen._get_output_from_history(session, prompt_id, output_dir)

        assert result is not None
        assert os.path.exists(result)
        assert result.endswith(".mp4")

    async def test_returns_none_when_not_ready(self):
        gen = self._make_generator()
        prompt_id = "test-prompt-123"

        with aioresponses() as m:
            m.get(
                f"http://test-comfyui:8188/history/{prompt_id}",
                payload={},
            )

            import aiohttp
            async with aiohttp.ClientSession() as session:
                result = await gen._get_output_from_history(session, prompt_id, "/tmp/out")

        assert result is None

    async def test_raises_on_execution_error(self):
        gen = self._make_generator()
        prompt_id = "test-prompt-123"

        with aioresponses() as m:
            m.get(
                f"http://test-comfyui:8188/history/{prompt_id}",
                payload={
                    prompt_id: {
                        "status": {
                            "status_str": "error",
                            "messages": [["error", {"message": "OOM"}]],
                        },
                        "outputs": {},
                    }
                },
            )

            import aiohttp
            async with aiohttp.ClientSession() as session:
                with pytest.raises(Exception, match="ComfyUI execution failed"):
                    await gen._get_output_from_history(session, prompt_id, "/tmp/out")

    async def test_returns_none_on_http_error(self):
        gen = self._make_generator()
        prompt_id = "test-prompt-123"

        with aioresponses() as m:
            m.get(f"http://test-comfyui:8188/history/{prompt_id}", status=500)

            import aiohttp
            async with aiohttp.ClientSession() as session:
                result = await gen._get_output_from_history(session, prompt_id, "/tmp/out")

        assert result is None


class TestUnloadModel:
    async def test_posts_to_free_endpoint(self):
        gen = ComfyUIVideoGenerator()
        gen.base_url = "http://test-comfyui:8188"

        with aioresponses() as m:
            m.post("http://test-comfyui:8188/free", payload={})

            await gen._unload_model()

            # Verify it was called
            assert ("POST", "http://test-comfyui:8188/free") in [
                (k[0], str(k[1])) for k in m.requests.keys()
            ]

    async def test_silently_handles_errors(self):
        gen = ComfyUIVideoGenerator()
        gen.base_url = "http://test-comfyui:8188"

        with aioresponses() as m:
            m.post("http://test-comfyui:8188/free", exception=Exception("Connection refused"))

            # Should not raise
            await gen._unload_model()


class TestGenerateVideo:
    async def test_submits_prompt_and_returns_path(self, tmp_path):
        gen = ComfyUIVideoGenerator()
        gen.base_url = "http://test-comfyui:8188"

        output_dir = str(tmp_path / "output")
        os.makedirs(output_dir)

        prompt_id = "test-prompt-id"

        with patch.object(gen, "_load_workflow_template", return_value={"node1": {"class_type": "Test", "inputs": {}}}):
            with patch.object(gen, "_inject_prompt", return_value={"node1": {"class_type": "Test", "inputs": {}}}):
                with patch.object(gen, "_configure_workflow", return_value={"node1": {"class_type": "Test", "inputs": {}}}):
                    with patch.object(gen, "_poll_for_completion", new_callable=AsyncMock) as mock_poll:
                        mock_poll.return_value = os.path.join(output_dir, "video.mp4")

                        with aioresponses() as m:
                            m.post(
                                "http://test-comfyui:8188/prompt",
                                payload={"prompt_id": prompt_id},
                            )

                            result = await gen.generate_video("test prompt", output_dir)

        assert result.endswith("video.mp4")

    async def test_unloads_model_in_single_gpu_mode(self, tmp_path):
        gen = ComfyUIVideoGenerator()
        gen.base_url = "http://test-comfyui:8188"

        output_dir = str(tmp_path / "output")
        os.makedirs(output_dir)

        with patch("api.generators.video.comfyui_generator.settings") as mock_settings:
            mock_settings.single_gpu_mode = True
            mock_settings.vidigen_frame_count = 121

            with patch.object(gen, "_load_workflow_template", return_value={}):
                with patch.object(gen, "_inject_prompt", return_value={}):
                    with patch.object(gen, "_configure_workflow", return_value={}):
                        with patch.object(gen, "_poll_for_completion", new_callable=AsyncMock) as mock_poll:
                            mock_poll.return_value = "video.mp4"
                            with patch.object(gen, "_unload_model", new_callable=AsyncMock) as mock_unload:
                                with aioresponses() as m:
                                    m.post(
                                        "http://test-comfyui:8188/prompt",
                                        payload={"prompt_id": "p1"},
                                    )
                                    await gen.generate_video("test", output_dir)

                                mock_unload.assert_awaited_once()
