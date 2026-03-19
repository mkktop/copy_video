"""File system service for browsing and managing video files"""
import os
from pathlib import Path
from typing import List, Optional
import mimetypes

from app.config import VIDEO_EXTENSIONS, WORKSPACE_DIR


def get_file_info(path: Path, base_dir: Path) -> dict:
    """Get file information as dictionary"""
    try:
        stat = path.stat()
        return {
            "path": str(path.relative_to(base_dir)),
            "name": path.name,
            "size": stat.st_size if path.is_file() else 0,
            "extension": path.suffix.lower(),
            "is_dir": path.is_dir(),
            "modified": stat.st_mtime
        }
    except Exception:
        return {
            "path": str(path.relative_to(base_dir)),
            "name": path.name,
            "size": 0,
            "extension": "",
            "is_dir": path.is_dir(),
            "modified": 0
        }


def browse_directory(relative_path: str = "", base_dir: Optional[Path] = None) -> dict:
    """
    Browse a directory and return its contents.

    Args:
        relative_path: Relative path from base directory
        base_dir: Base directory to browse from (defaults to WORKSPACE_DIR)
    """
    if base_dir is None:
        base_dir = WORKSPACE_DIR

    # Ensure we don't escape base directory
    target_path = (base_dir / relative_path).resolve()
    try:
        target_path = target_path.relative_to(base_dir.resolve())
    except ValueError:
        # Path escapes base directory
        target_path = Path(".")

    full_path = base_dir / target_path

    if not full_path.exists():
        full_path = base_dir

    if not full_path.is_dir():
        return {
            "path": ".",
            "files": [],
            "parent": None
        }

    files = []
    try:
        for item in sorted(full_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            info = get_file_info(item, base_dir)
            # Only include video files and directories
            if info["is_dir"] or info["extension"] in VIDEO_EXTENSIONS:
                files.append(info)

        # Get parent directory
        try:
            parent = str(target_path.parent) if str(target_path) != "." else None
        except ValueError:
            parent = None

        return {
            "path": str(target_path),
            "files": files,
            "parent": parent
        }
    except PermissionError:
        return {
            "path": str(target_path),
            "files": [],
            "parent": None,
            "error": "Permission denied"
        }


def resolve_path(path: str, base_dir: Optional[Path] = None) -> Path:
    """Resolve a path relative to base directory"""
    if base_dir is None:
        base_dir = WORKSPACE_DIR
    return (base_dir / path).resolve()


def is_video_file(path: Path) -> bool:
    """Check if a file is a video file"""
    return path.suffix.lower() in VIDEO_EXTENSIONS


def scan_videos(directory: Path) -> List[Path]:
    """Recursively scan directory for video files"""
    videos = []
    try:
        for item in directory.rglob("*"):
            if item.is_file() and is_video_file(item):
                videos.append(item)
    except PermissionError:
        pass
    return videos


def get_video_info(path: Path) -> dict:
    """Get detailed video file information"""
    if not path.exists() or not is_video_file(path):
        return {}

    stat = path.stat()
    return {
        "name": path.name,
        "path": str(path),
        "size": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "extension": path.suffix.lower(),
        "modified": stat.st_mtime
    }
