import asyncio
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from api.config import settings

class CleanupScheduler:
    """Background task to delete generated videos older than 24 hours"""

    def __init__(self, videos_dir: Path, retention_hours: int = 24):
        self.videos_dir = videos_dir
        self.retention_hours = retention_hours
        self.running = False

    async def start(self):
        """Start the cleanup scheduler"""
        self.running = True

        while self.running:
            try:
                await self._cleanup_old_files()
            except Exception as e:
                print(f"Cleanup error: {e}")

            # Run cleanup every hour
            await asyncio.sleep(3600)

    async def _cleanup_old_files(self):
        """Delete folders older than retention period"""

        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        cutoff_timestamp = cutoff_time.timestamp()

        deleted_count = 0

        for folder in self.videos_dir.iterdir():
            if not folder.is_dir():
                continue

            # Check folder modification time
            folder_mtime = folder.stat().st_mtime

            if folder_mtime < cutoff_timestamp:
                # Delete folder and all contents
                for file in folder.rglob("*"):
                    if file.is_file():
                        file.unlink()

                folder.rmdir()
                deleted_count += 1
                print(f"Deleted old folder: {folder.name}")

        if deleted_count > 0:
            print(f"Cleanup complete: {deleted_count} folders deleted")

    def stop(self):
        """Stop the cleanup scheduler"""
        self.running = False
