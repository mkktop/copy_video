"""Pydantic models for API requests/responses"""
from pydantic import BaseModel
from typing import Optional


class MetadataConfig(BaseModel):
    """Custom metadata configuration for video transcoding"""
    title: Optional[str] = None
    author: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    comment: Optional[str] = None
    description: Optional[str] = None
    copyright: Optional[str] = None
    genre: Optional[str] = None
    custom: Optional[dict[str, str]] = None  # Custom key-value pairs


class TranscodeRequest(BaseModel):
    input_path: str
    output_path: Optional[str] = None
    output_dir: Optional[str] = None
    metadata: Optional[MetadataConfig] = None  # Custom metadata


class TaskResponse(BaseModel):
    id: int
    input_path: str
    output_path: str
    status: str
    progress: float
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    metadata: Optional[dict] = None


class FileInfo(BaseModel):
    path: str
    name: str
    size: int
    extension: str
    is_dir: bool = False


class DirectoryInfo(BaseModel):
    path: str
    files: list[FileInfo]
    parent: Optional[str] = None
