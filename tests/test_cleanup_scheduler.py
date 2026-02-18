import os
import time
import pytest
from pathlib import Path
from api.cleanup_scheduler import CleanupScheduler


class TestCleanupOldFiles:
    async def test_deletes_old_folders(self, tmp_path):
        """Folders older than retention period should be deleted."""
        scheduler = CleanupScheduler(videos_dir=tmp_path, retention_hours=24)

        # Create an old folder (set mtime to 48 hours ago)
        old_folder = tmp_path / "old_video"
        old_folder.mkdir()
        old_file = old_folder / "video.mp4"
        old_file.write_text("fake video data")
        old_time = time.time() - (48 * 3600)
        os.utime(old_folder, (old_time, old_time))

        await scheduler._cleanup_old_files()

        assert not old_folder.exists()

    async def test_preserves_recent_folders(self, tmp_path):
        """Folders newer than retention period should be kept."""
        scheduler = CleanupScheduler(videos_dir=tmp_path, retention_hours=24)

        # Create a recent folder (default mtime is now)
        recent_folder = tmp_path / "recent_video"
        recent_folder.mkdir()
        recent_file = recent_folder / "video.mp4"
        recent_file.write_text("fake video data")

        await scheduler._cleanup_old_files()

        assert recent_folder.exists()
        assert recent_file.exists()

    async def test_mixed_old_and_new(self, tmp_path):
        """Only old folders should be deleted, recent ones preserved."""
        scheduler = CleanupScheduler(videos_dir=tmp_path, retention_hours=24)

        # Old folder
        old_folder = tmp_path / "old"
        old_folder.mkdir()
        (old_folder / "file.mp4").write_text("old")
        old_time = time.time() - (48 * 3600)
        os.utime(old_folder, (old_time, old_time))

        # Recent folder
        new_folder = tmp_path / "new"
        new_folder.mkdir()
        (new_folder / "file.mp4").write_text("new")

        await scheduler._cleanup_old_files()

        assert not old_folder.exists()
        assert new_folder.exists()

    async def test_handles_empty_directory(self, tmp_path):
        """Should not error on empty videos directory."""
        scheduler = CleanupScheduler(videos_dir=tmp_path, retention_hours=24)
        await scheduler._cleanup_old_files()  # Should not raise

    async def test_skips_files_in_root(self, tmp_path):
        """Files (not directories) in the root should be skipped."""
        scheduler = CleanupScheduler(videos_dir=tmp_path, retention_hours=24)

        stray_file = tmp_path / "stray.txt"
        stray_file.write_text("not a folder")
        old_time = time.time() - (48 * 3600)
        os.utime(stray_file, (old_time, old_time))

        await scheduler._cleanup_old_files()

        assert stray_file.exists()  # Should be skipped, not deleted

    async def test_custom_retention_hours(self, tmp_path):
        """Custom retention period should be respected."""
        scheduler = CleanupScheduler(videos_dir=tmp_path, retention_hours=1)

        folder = tmp_path / "recent_but_old_for_1h"
        folder.mkdir()
        (folder / "file.mp4").write_text("data")
        # Set mtime to 2 hours ago
        old_time = time.time() - (2 * 3600)
        os.utime(folder, (old_time, old_time))

        await scheduler._cleanup_old_files()

        assert not folder.exists()


class TestCleanupSchedulerLifecycle:
    def test_stop_sets_running_false(self, tmp_path):
        scheduler = CleanupScheduler(videos_dir=tmp_path)
        scheduler.running = True
        scheduler.stop()
        assert scheduler.running is False

    def test_default_retention(self, tmp_path):
        scheduler = CleanupScheduler(videos_dir=tmp_path)
        assert scheduler.retention_hours == 24
