"""Scheduler service for auto-scanning and transcoding"""
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.models.settings import TranscodeSettings
from app.services.settings_service import settings_service
from app.services.ffmpeg import transcode_video_async, verify_output
from app.services.file_service import scan_videos, is_video_file
from app.config import VIDEO_EXTENSIONS


class SchedulerService:
    """Background scheduler for auto-scan and transcode"""

    def __init__(self):
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.current_transcode = None

    async def start(self):
        """Start the scheduler"""
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._run_loop())

    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def _run_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                settings = settings_service.load_settings()

                if settings.auto_scan_enabled:
                    await self._scan_and_transcode(settings)

                # Wait for next scan
                await asyncio.sleep(settings.auto_scan_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Scheduler error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _scan_and_transcode(self, settings: TranscodeSettings):
        """Scan directory and transcode new files"""
        scan_dir = Path(settings.scan_input_dir)

        if not scan_dir.exists():
            return

        # Scan for video files
        video_files = scan_videos(scan_dir)

        for video_file in video_files:
            if not self.running:
                break

            # Check if already scanned
            file_key = str(video_file)
            if settings_service.is_file_scanned(file_key):
                continue

            # Transcode the file
            await self._auto_transcode(video_file, settings)

            # Mark as scanned
            settings_service.add_scanned_file(file_key)

    async def _auto_transcode(self, input_path: Path, settings: TranscodeSettings):
        """Auto transcode a file"""
        try:
            # Generate output path
            input_name = input_path.stem
            output_dir = Path(settings.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{input_name}_transcoded{input_path.suffix}"

            print(f"[{datetime.now()}] Auto transcoding: {input_path.name}")

            # Build metadata from settings
            metadata = {}
            if settings.metadata_title:
                metadata["title"] = settings.metadata_title
            if settings.metadata_author:
                metadata["author"] = settings.metadata_author
            if settings.metadata_album:
                metadata["album"] = settings.metadata_album
            if settings.metadata_year:
                metadata["year"] = settings.metadata_year
            if settings.metadata_comment:
                metadata["comment"] = settings.metadata_comment
            if settings.metadata_description:
                metadata["description"] = settings.metadata_description
            if settings.metadata_copyright:
                metadata["copyright"] = settings.metadata_copyright
            if settings.metadata_genre:
                metadata["genre"] = settings.metadata_genre
            if settings.metadata_custom:
                import json
                try:
                    metadata["custom"] = json.loads(settings.metadata_custom)
                except:
                    pass

            # Run transcode
            success = True
            async for update in transcode_video_async(str(input_path), str(output_path), custom_metadata=metadata):
                if update["status"] == "error":
                    print(f"Error transcoding {input_path.name}: {update.get('message')}")
                    success = False
                    break

            if success and verify_output(str(output_path)):
                print(f"[{datetime.now()}] Successfully transcoded: {input_path.name} -> {output_path.name}")

                # Delete source if configured
                if settings.delete_source:
                    try:
                        input_path.unlink()
                        print(f"[{datetime.now()}] Deleted source: {input_path.name}")
                    except Exception as e:
                        print(f"Error deleting source: {e}")
            else:
                print(f"[{datetime.now()}] Failed to transcode: {input_path.name}")

        except Exception as e:
            print(f"Error in auto transcode: {e}")

    def get_status(self) -> dict:
        """Get scheduler status"""
        settings = settings_service.load_settings()
        return {
            "running": self.running,
            "enabled": settings.auto_scan_enabled,
            "interval": settings.auto_scan_interval,
            "scan_dir": settings.scan_input_dir,
            "scanned_count": len(settings.scanned_files)
        }


# Global scheduler instance
scheduler_service = SchedulerService()
