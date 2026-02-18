from fastapi import WebSocket
from typing import Dict, Set
import asyncio

class ConnectionManager:
    """Manage WebSocket connections for real-time progress updates"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        self.active_connections[job_id].add(websocket)

    def disconnect(self, job_id: str, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            # Clean up empty sets
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def send_progress(
        self,
        job_id: str,
        progress: float,
        stage: str,
        message: str
    ):
        """
        Send progress update to all connected clients for a job

        Args:
            job_id: Unique job identifier
            progress: Progress percentage (0-100)
            stage: Current stage name ("expansion", "generation", "captions", "overlay", "complete", "error")
            message: Human-readable status message
        """
        if job_id in self.active_connections:
            data = {
                "type": "progress",
                "progress": progress,
                "stage": stage,
                "message": message
            }

            disconnected = set()
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(data)
                except Exception:
                    disconnected.add(connection)

            # Remove disconnected clients
            for conn in disconnected:
                self.disconnect(job_id, conn)

# Global instance
manager = ConnectionManager()
