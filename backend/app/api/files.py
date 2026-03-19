"""File browsing API endpoints"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.services.file_service import browse_directory, resolve_path, get_video_info
from app.models.task import DirectoryInfo
from app.config import WORKSPACE_DIR

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/browse", response_model=DirectoryInfo)
async def browse_files(path: str = ""):
    """Browse files in the workspace directory"""
    result = browse_directory(path, WORKSPACE_DIR)
    if "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
    return result


@router.get("/info")
async def get_file_info(path: str):
    """Get information about a specific file"""
    try:
        resolved = resolve_path(path, WORKSPACE_DIR)
        if not resolved.exists():
            raise HTTPException(status_code=404, detail="File not found")
        return get_video_info(resolved)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")


@router.get("/validate-path")
async def validate_path(path: str):
    """Validate if a path is accessible within workspace"""
    try:
        resolved = resolve_path(path, WORKSPACE_DIR)
        return {
            "valid": True,
            "exists": resolved.exists(),
            "is_dir": resolved.is_dir() if resolved.exists() else None,
            "path": str(resolved)
        }
    except ValueError:
        return {"valid": False, "exists": False}
