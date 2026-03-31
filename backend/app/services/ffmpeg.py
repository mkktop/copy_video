"""FFmpeg service for video transcoding"""
import asyncio
import subprocess
import re
import uuid
from pathlib import Path
from typing import Generator, Optional, Dict, AsyncGenerator
from datetime import datetime

from app.config import FFMPEG_PATH, FFMPEG_TIMEOUT


def get_video_duration(input_path: str) -> Optional[float]:
    """Get video duration in seconds using ffprobe"""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(input_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        pass
    return None


def parse_progress(line: str, duration: float) -> Optional[float]:
    """Parse FFmpeg progress output and return percentage"""
    # Match: time=00:00:15.23
    match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
    if match:
        hours, mins, secs = map(float, match.groups())
        current_time = hours * 3600 + mins * 60 + secs
        if duration and duration > 0:
            return min(100, (current_time / duration) * 100)
    return None


def transcode_video(input_path: str, output_path: str,
                   progress_callback=None, custom_metadata: Optional[Dict] = None) -> Generator[dict, None, bool]:
    """
    Transcode video using FFmpeg with stream copy and metadata modification.

    This changes the file hash by:
    1. Adding/modifying metadata (title, author, comment, etc.)
    2. Reorganizing container with movflags +faststart

    Args:
        input_path: Input video file path
        output_path: Output video file path
        progress_callback: Optional callback for progress updates
        custom_metadata: Optional dict of custom metadata to apply

    Yields:
        dict: Progress updates with 'progress' and 'status' keys

    Returns:
        bool: True if successful, False otherwise
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        yield {"status": "error", "message": f"Input file not found: {input_path}"}
        return False

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get video duration for progress calculation
    duration = get_video_duration(input_path)

    # Build metadata list
    metadata = []

    # Add custom metadata if provided
    if custom_metadata:
        # Standard metadata fields
        if custom_metadata.get("title"):
            metadata.extend(["-metadata", f"title={custom_metadata['title']}"])
        if custom_metadata.get("author"):
            metadata.extend(["-metadata", f"artist={custom_metadata['author']}"])
        if custom_metadata.get("album"):
            metadata.extend(["-metadata", f"album={custom_metadata['album']}"])
        if custom_metadata.get("year"):
            metadata.extend(["-metadata", f"date={custom_metadata['year']}"])
        if custom_metadata.get("comment"):
            metadata.extend(["-metadata", f"comment={custom_metadata['comment']}"])
        if custom_metadata.get("description"):
            metadata.extend(["-metadata", f"description={custom_metadata['description']}"])
        if custom_metadata.get("copyright"):
            metadata.extend(["-metadata", f"copyright={custom_metadata['copyright']}"])
        if custom_metadata.get("genre"):
            metadata.extend(["-metadata", f"genre={custom_metadata['genre']}"])

        # Custom key-value pairs
        if custom_metadata.get("custom"):
            for key, value in custom_metadata["custom"].items():
                if value:  # Only add non-empty values
                    metadata.extend(["-metadata", f"{key}={value}"])

    # Always add a random identifier to ensure hash changes
    random_uuid = str(uuid.uuid4())
    metadata.extend([
        "-metadata", f"encoder=CopyVideo-{random_uuid[:8]}",
        "-metadata", f"transcoded_at={datetime.now().isoformat()}"
    ])

    # Build FFmpeg command
    cmd = [
        FFMPEG_PATH,
        "-i", str(input_path),
        "-map", "0",  # Map all streams (video, audio, subtitles, attachments)
        "-c", "copy",  # Copy streams without re-encoding
        *metadata,     # Add new metadata
        "-movflags", "+faststart",  # Reorganize container
        "-y",  # Overwrite output
        str(output_path)
    ]

    yield {"status": "starting", "progress": 0}

    try:
        # Run FFmpeg and capture stderr for progress
        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        last_progress = 0
        for line in process.stderr:
            progress = parse_progress(line, duration)
            if progress is not None and abs(progress - last_progress) > 1:
                last_progress = progress
                yield {"status": "processing", "progress": progress}
                if progress_callback:
                    progress_callback(progress)

        # Wait for process to complete
        returncode = process.wait(timeout=FFMPEG_TIMEOUT)

        if returncode == 0:
            yield {"status": "completed", "progress": 100}
            return True
        else:
            yield {"status": "error", "message": f"FFmpeg exited with code {returncode}"}
            return False

    except subprocess.TimeoutExpired:
        process.kill()
        yield {"status": "error", "message": "Transcode timeout"}
        return False
    except Exception as e:
        yield {"status": "error", "message": str(e)}
        return False


def verify_output(output_path: str) -> bool:
    """Verify that output file exists and has content"""
    path = Path(output_path)
    return path.exists() and path.stat().st_size > 0


def _build_metadata_args(custom_metadata: Optional[Dict] = None) -> list:
    """Build FFmpeg metadata arguments"""
    metadata = []

    if custom_metadata:
        if custom_metadata.get("title"):
            metadata.extend(["-metadata", f"title={custom_metadata['title']}"])
        if custom_metadata.get("author"):
            metadata.extend(["-metadata", f"artist={custom_metadata['author']}"])
        if custom_metadata.get("album"):
            metadata.extend(["-metadata", f"album={custom_metadata['album']}"])
        if custom_metadata.get("year"):
            metadata.extend(["-metadata", f"date={custom_metadata['year']}"])
        if custom_metadata.get("comment"):
            metadata.extend(["-metadata", f"comment={custom_metadata['comment']}"])
        if custom_metadata.get("description"):
            metadata.extend(["-metadata", f"description={custom_metadata['description']}"])
        if custom_metadata.get("copyright"):
            metadata.extend(["-metadata", f"copyright={custom_metadata['copyright']}"])
        if custom_metadata.get("genre"):
            metadata.extend(["-metadata", f"genre={custom_metadata['genre']}"])

        if custom_metadata.get("custom"):
            for key, value in custom_metadata["custom"].items():
                if value:
                    metadata.extend(["-metadata", f"{key}={value}"])

    random_uuid = str(uuid.uuid4())
    metadata.extend([
        "-metadata", f"encoder=CopyVideo-{random_uuid[:8]}",
        "-metadata", f"transcoded_at={datetime.now().isoformat()}"
    ])

    return metadata


async def transcode_video_async(
    input_path: str,
    output_path: str,
    cancel_event: Optional[asyncio.Event] = None,
    progress_callback=None,
    custom_metadata: Optional[Dict] = None
) -> AsyncGenerator[dict, None]:
    """
    Async version of transcode_video using asyncio.create_subprocess_exec.

    Supports cancellation via cancel_event. Yields progress updates.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        yield {"status": "error", "message": f"Input file not found: {input_path}"}
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    duration = await asyncio.to_thread(get_video_duration, str(input_path))
    metadata = _build_metadata_args(custom_metadata)

    cmd = [
        FFMPEG_PATH,
        "-i", str(input_path),
        "-map", "0",
        "-c", "copy",
        *metadata,
        "-movflags", "+faststart",
        "-y",
        str(output_path)
    ]

    yield {"status": "starting", "progress": 0}

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE
        )

        last_progress = 0

        while True:
            # Check cancellation
            if cancel_event and cancel_event.is_set():
                process.kill()
                await process.wait()
                yield {"status": "cancelled"}
                return

            try:
                line = await asyncio.wait_for(
                    process.stderr.readline(), timeout=1.0
                )
            except asyncio.TimeoutError:
                # Timeout on readline, loop back to check cancel_event
                continue

            if not line:
                break

            line_str = line.decode(errors="replace").strip()
            progress = parse_progress(line_str, duration)
            if progress is not None and abs(progress - last_progress) > 1:
                last_progress = progress
                yield {"status": "processing", "progress": progress}
                if progress_callback:
                    progress_callback(progress)

        # Check cancellation one more time before finalizing
        if cancel_event and cancel_event.is_set():
            yield {"status": "cancelled"}
            return

        returncode = await process.wait()

        if returncode == 0:
            yield {"status": "completed", "progress": 100}
        else:
            yield {"status": "error", "message": f"FFmpeg exited with code {returncode}"}

    except asyncio.CancelledError:
        try:
            process.kill()
            await process.wait()
        except Exception:
            pass
        yield {"status": "cancelled"}
    except Exception as e:
        yield {"status": "error", "message": str(e)}
