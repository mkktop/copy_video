"""Settings models for configuration persistence"""
from pydantic import BaseModel
from typing import Optional, List


class TranscodeSettings(BaseModel):
    """Transcode configuration settings"""
    # Output settings
    output_dir: str = "/app/workspace/output"
    delete_source: bool = False  # Delete source file after successful transcode

    # Auto-scan settings
    auto_scan_enabled: bool = False
    auto_scan_interval: int = 3600  # seconds
    scan_input_dir: str = "/app/workspace/input"

    # Metadata settings (saved for reuse)
    metadata_title: Optional[str] = None
    metadata_author: Optional[str] = None
    metadata_album: Optional[str] = None
    metadata_year: Optional[int] = None
    metadata_comment: Optional[str] = None
    metadata_description: Optional[str] = None
    metadata_copyright: Optional[str] = None
    metadata_genre: Optional[str] = None
    metadata_custom: Optional[str] = None  # JSON string

    # Scan history (to avoid re-scanning same files)
    scanned_files: List[str] = []


class ScheduleConfig(BaseModel):
    """Schedule configuration for auto-scan"""
    enabled: bool
    interval_seconds: int
    input_dir: str
    output_dir: str
