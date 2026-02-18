import pytest
from unittest.mock import AsyncMock, MagicMock


class TestConnectionManager:
    def _make_manager(self):
        from api.websocket_manager import ConnectionManager
        return ConnectionManager()

    def _make_mock_ws(self):
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    async def test_connect_accepts_and_registers(self):
        mgr = self._make_manager()
        ws = self._make_mock_ws()

        await mgr.connect("job-1", ws)

        ws.accept.assert_awaited_once()
        assert ws in mgr.active_connections["job-1"]

    async def test_connect_multiple_clients(self):
        mgr = self._make_manager()
        ws1 = self._make_mock_ws()
        ws2 = self._make_mock_ws()

        await mgr.connect("job-1", ws1)
        await mgr.connect("job-1", ws2)

        assert len(mgr.active_connections["job-1"]) == 2

    async def test_disconnect_removes_connection(self):
        mgr = self._make_manager()
        ws = self._make_mock_ws()

        await mgr.connect("job-1", ws)
        mgr.disconnect("job-1", ws)

        assert "job-1" not in mgr.active_connections

    async def test_disconnect_cleans_up_empty_set(self):
        mgr = self._make_manager()
        ws = self._make_mock_ws()

        await mgr.connect("job-1", ws)
        mgr.disconnect("job-1", ws)

        assert "job-1" not in mgr.active_connections

    async def test_disconnect_preserves_other_connections(self):
        mgr = self._make_manager()
        ws1 = self._make_mock_ws()
        ws2 = self._make_mock_ws()

        await mgr.connect("job-1", ws1)
        await mgr.connect("job-1", ws2)
        mgr.disconnect("job-1", ws1)

        assert ws2 in mgr.active_connections["job-1"]
        assert ws1 not in mgr.active_connections["job-1"]

    async def test_disconnect_nonexistent_job(self):
        mgr = self._make_manager()
        ws = self._make_mock_ws()
        mgr.disconnect("no-such-job", ws)  # Should not raise

    async def test_send_progress_broadcasts(self):
        mgr = self._make_manager()
        ws1 = self._make_mock_ws()
        ws2 = self._make_mock_ws()

        await mgr.connect("job-1", ws1)
        await mgr.connect("job-1", ws2)

        await mgr.send_progress("job-1", 50.0, "generation", "Generating...")

        expected_data = {
            "type": "progress",
            "progress": 50.0,
            "stage": "generation",
            "message": "Generating...",
        }
        ws1.send_json.assert_awaited_once_with(expected_data)
        ws2.send_json.assert_awaited_once_with(expected_data)

    async def test_send_progress_removes_dead_connections(self):
        mgr = self._make_manager()
        good_ws = self._make_mock_ws()
        dead_ws = self._make_mock_ws()
        dead_ws.send_json.side_effect = Exception("Connection closed")

        await mgr.connect("job-1", good_ws)
        await mgr.connect("job-1", dead_ws)

        await mgr.send_progress("job-1", 50.0, "test", "msg")

        assert dead_ws not in mgr.active_connections.get("job-1", set())
        assert good_ws in mgr.active_connections["job-1"]

    async def test_send_progress_no_connections(self):
        mgr = self._make_manager()
        # Should not raise when no connections exist
        await mgr.send_progress("no-job", 50.0, "test", "msg")

    async def test_send_progress_all_dead(self):
        mgr = self._make_manager()
        dead_ws = self._make_mock_ws()
        dead_ws.send_json.side_effect = Exception("Connection closed")

        await mgr.connect("job-1", dead_ws)
        await mgr.send_progress("job-1", 50.0, "test", "msg")

        assert "job-1" not in mgr.active_connections
