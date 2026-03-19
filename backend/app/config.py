"""Application configuration"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path("/app/data")
WORKSPACE_DIR = Path("/app/workspace")

# Default paths (can be overridden via API)
DEFAULT_INPUT_DIR = WORKSPACE_DIR / "input"
DEFAULT_OUTPUT_DIR = WORKSPACE_DIR / "output"

# Video file extensions to scan
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm", ".m4v"}

# Database
DATABASE_URL = f"sqlite:///{DATA_DIR}/copy_video.db"

# FFmpeg settings
FFMPEG_PATH = "ffmpeg"
FFMPEG_TIMEOUT = 3600  # 1 hour max per video

# Create directories if they don't exist
for dir_path in [DATA_DIR, DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
