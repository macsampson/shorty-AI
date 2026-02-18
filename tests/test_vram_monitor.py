import pytest
from unittest.mock import patch, MagicMock
import subprocess


class TestGetVramUsage:
    @patch("api.vram_monitor.subprocess.run")
    def test_parses_nvidia_smi_output(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="4096, 24576\n",
        )

        from api.vram_monitor import get_vram_usage
        result = get_vram_usage()

        assert result["allocated_gb"] == 4.0
        assert result["total_gb"] == 24.0
        assert result["free_gb"] == 20.0
        assert result["reserved_gb"] == 4.0

    @patch("api.vram_monitor.subprocess.run")
    def test_rtx_3090_values(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="2150, 24576\n",
        )

        from api.vram_monitor import get_vram_usage
        result = get_vram_usage()

        assert result["total_gb"] == 24.0
        assert result["allocated_gb"] == 2.1
        assert result["free_gb"] == 21.9

    @patch("api.vram_monitor.subprocess.run")
    def test_nonzero_returncode(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")

        from api.vram_monitor import get_vram_usage
        result = get_vram_usage()

        assert result == {"allocated_gb": 0, "reserved_gb": 0, "total_gb": 0, "free_gb": 0}

    @patch("api.vram_monitor.subprocess.run", side_effect=FileNotFoundError)
    def test_nvidia_smi_not_found(self, mock_run):
        from api.vram_monitor import get_vram_usage
        result = get_vram_usage()

        assert result == {"allocated_gb": 0, "reserved_gb": 0, "total_gb": 0, "free_gb": 0}

    @patch("api.vram_monitor.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="nvidia-smi", timeout=5))
    def test_nvidia_smi_timeout(self, mock_run):
        from api.vram_monitor import get_vram_usage
        result = get_vram_usage()

        assert result == {"allocated_gb": 0, "reserved_gb": 0, "total_gb": 0, "free_gb": 0}


class TestWaitForVram:
    @patch("api.vram_monitor.get_vram_usage")
    async def test_returns_true_when_enough_vram(self, mock_usage):
        mock_usage.return_value = {"free_gb": 20.0}

        from api.vram_monitor import wait_for_vram
        result = await wait_for_vram(min_free_gb=10.0, timeout=5)

        assert result is True

    @patch("api.vram_monitor.get_vram_usage")
    async def test_polls_until_available(self, mock_usage):
        # First two calls: not enough VRAM, third call: enough
        mock_usage.side_effect = [
            {"free_gb": 2.0},
            {"free_gb": 5.0},
            {"free_gb": 15.0},
        ]

        from api.vram_monitor import wait_for_vram
        result = await wait_for_vram(min_free_gb=10.0, timeout=30)

        assert result is True

    @patch("api.vram_monitor.asyncio.sleep")
    @patch("api.vram_monitor.time.time")
    @patch("api.vram_monitor.get_vram_usage")
    async def test_returns_false_on_timeout(self, mock_usage, mock_time, mock_sleep):
        mock_usage.return_value = {"free_gb": 1.0}
        # Simulate time passing beyond timeout
        mock_time.side_effect = [0, 0, 5, 10, 15]
        mock_sleep.return_value = None

        from api.vram_monitor import wait_for_vram
        result = await wait_for_vram(min_free_gb=10.0, timeout=10)

        assert result is False
