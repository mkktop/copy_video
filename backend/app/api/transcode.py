"""Transcode API endpoints"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Optional, Dict
import json
from pathlib import Path

from app.models.task import TranscodeRequest, TaskResponse, MetadataConfig
from app.services.ffmpeg import transcode_video, verify_output
from app.services.settings_service import settings_service
from app.db.database import db
from app.config import DEFAULT_OUTPUT_DIR

router = APIRouter(prefix="/api/transcode", tags=["transcode"])


# Store active transcode processes for cancellation
active_transcodes: Dict[int, bool] = {}


def metadata_to_dict(metadata: Optional[MetadataConfig]) -> Optional[dict]:
    """Convert MetadataConfig to dict for FFmpeg"""
    if not metadata:
        return None
    result = {}
    if metadata.title:
        result["title"] = metadata.title
    if metadata.author:
        result["author"] = metadata.author
    if metadata.album:
        result["album"] = metadata.album
    if metadata.year:
        result["year"] = metadata.year
    if metadata.comment:
        result["comment"] = metadata.comment
    if metadata.description:
        result["description"] = metadata.description
    if metadata.copyright:
        result["copyright"] = metadata.copyright
    if metadata.genre:
        result["genre"] = metadata.genre
    if metadata.custom:
        result["custom"] = metadata.custom
    return result if result else None


def update_task_progress(task_id: int, progress: float):
    """Update task progress in database"""
    db.update_task(task_id, progress=progress)


@router.post("/start", response_model=TaskResponse)
async def start_transcode(request: TranscodeRequest):
    """Start a new transcode task"""
    # Convert metadata to dict
    metadata_dict = metadata_to_dict(request.metadata)

    # Determine output path
    if request.output_path:
        output_path = request.output_path
    elif request.output_dir:
        input_name = Path(request.input_path).stem
        output_path = str(Path(request.output_dir) / f"{input_name}_transcoded{Path(request.input_path).suffix}")
    else:
        input_name = Path(request.input_path).stem
        output_path = str(DEFAULT_OUTPUT_DIR / f"{input_name}_transcoded{Path(request.input_path).suffix}")

    # Create task in database with metadata
    task = db.create_task(request.input_path, output_path, metadata_dict)

    # Store metadata for this task (for progress stream to use)
    if metadata_dict:
        active_transcodes[task.id] = {"active": True, "metadata": metadata_dict}
    else:
        active_transcodes[task.id] = {"active": True, "metadata": None}

    # Update status to processing
    db.update_task(task.id, status="processing")

    # Run transcode (will be async in production)
    return TaskResponse(**task.to_dict())


@router.get("/progress/{task_id}")
async def get_transcode_progress(task_id: int):
    """Get current progress for a transcode task (SSE stream)"""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # If already completed, return result immediately
    if task.status in ["completed", "failed"]:
        return task.to_dict()

    # Get task metadata from active transcodes storage
    task_data = active_transcodes.get(task_id, {})
    custom_metadata = task_data.get("metadata") if isinstance(task_data, dict) else None

    # Run transcode and stream progress
    async def progress_stream():
        try:
            # Get fresh task data
            current_task = db.get_task(task_id)
            if not current_task:
                yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                return

            # Execute transcode with custom metadata
            for update in transcode_video(
                current_task.input_path,
                current_task.output_path,
                lambda p: db.update_task(task_id, progress=p),
                custom_metadata=custom_metadata
            ):
                # Update database with progress
                if update["status"] == "processing":
                    db.update_task(task_id, progress=update["progress"])

                # Send SSE update
                yield f"data: {json.dumps(update)}\n\n"

            # Finalize task status
            if verify_output(current_task.output_path):
                db.update_task(task_id, status="completed", progress=100, completed_at="completed")

                # Delete source file if configured
                settings = settings_service.load_settings()
                if settings.delete_source:
                    try:
                        source_path = Path(current_task.input_path)
                        if source_path.exists():
                            source_path.unlink()
                            yield f"data: {json.dumps({'status': 'info', 'message': 'Source file deleted'})}\n\n"
                    except Exception as e:
                        yield f"data: {json.dumps({'status': 'warning', 'message': f'Failed to delete source: {str(e)}'})}\n\n"
            else:
                db.update_task(task_id, status="failed", error="Output file verification failed")

            # Send final status
            final_task = db.get_task(task_id)
            yield f"data: {json.dumps({'status': 'done', 'task': final_task.to_dict()})}\n\n"

        except Exception as e:
            db.update_task(task_id, status="failed", error=str(e))
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
        finally:
            active_transcodes.pop(task_id, None)

    return StreamingResponse(
        progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(limit: int = 50):
    """List all transcode tasks"""
    tasks = db.get_all_tasks(limit)
    return [TaskResponse(**task.to_dict()) for task in tasks]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    """Get a specific task"""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**task.to_dict())


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: int):
    """Cancel a running transcode task"""
    if task_id in active_transcodes:
        task_data = active_transcodes[task_id]
        if isinstance(task_data, dict):
            task_data["active"] = False
        else:
            active_transcodes[task_id] = False
        db.update_task(task_id, status="cancelled")
        return {"message": "Task cancelled"}
    raise HTTPException(status_code=404, detail="Task not found or not running")
