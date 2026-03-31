"""Transcode API endpoints"""
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, Dict
import json
from pathlib import Path
from datetime import datetime

from app.models.task import TranscodeRequest, TaskResponse, MetadataConfig
from app.services.ffmpeg import transcode_video_async, verify_output
from app.services.settings_service import settings_service
from app.db.database import db
from app.config import DEFAULT_OUTPUT_DIR

router = APIRouter(prefix="/api/transcode", tags=["transcode"])

# Store active transcode tasks for cancellation
active_transcodes: Dict[int, dict] = {}


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


async def _run_transcode(task_id: int, input_path: str, output_path: str,
                         custom_metadata: Optional[dict] = None):
    """Background coroutine that runs the actual transcoding and updates DB."""
    cancel_event = asyncio.Event()
    active_transcodes[task_id] = {
        "cancel": cancel_event,
        "task": asyncio.current_task()
    }

    try:
        async for update in transcode_video_async(
            input_path, output_path,
            cancel_event=cancel_event,
            progress_callback=lambda p: db.update_task(task_id, progress=p),
            custom_metadata=custom_metadata
        ):
            status = update.get("status")

            if status == "processing":
                db.update_task(task_id, progress=update["progress"])

            elif status == "completed":
                if verify_output(output_path):
                    db.update_task(
                        task_id, status="completed", progress=100,
                        completed_at=datetime.now().isoformat()
                    )
                    settings = settings_service.load_settings()
                    if settings.delete_source:
                        try:
                            source_path = Path(input_path)
                            if source_path.exists():
                                source_path.unlink()
                        except Exception:
                            pass
                else:
                    db.update_task(
                        task_id, status="failed",
                        error="Output file verification failed"
                    )

            elif status == "error":
                db.update_task(
                    task_id, status="failed",
                    error=update.get("message", "Unknown error")
                )

            elif status == "cancelled":
                db.update_task(task_id, status="cancelled")
                return

    except asyncio.CancelledError:
        db.update_task(task_id, status="cancelled")
    except Exception as e:
        db.update_task(task_id, status="failed", error=str(e))
    finally:
        active_transcodes.pop(task_id, None)


@router.post("/start", response_model=TaskResponse)
async def start_transcode(request: TranscodeRequest):
    """Start a new transcode task"""
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

    # Create task in database
    task = db.create_task(request.input_path, output_path, metadata_dict)
    db.update_task(task.id, status="processing")

    # Start transcoding in background
    asyncio.create_task(
        _run_transcode(task.id, request.input_path, output_path, metadata_dict)
    )

    return TaskResponse(**task.to_dict())


@router.get("/progress/{task_id}")
async def get_transcode_progress(task_id: int):
    """SSE stream that polls DB for task progress updates"""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # If already in terminal state, return result immediately
    if task.status in ["completed", "failed", "cancelled"]:
        return task.to_dict()

    async def progress_stream():
        event_id = 0
        try:
            while True:
                current_task = db.get_task(task_id)
                if not current_task:
                    yield f"id: {event_id}\ndata: {json.dumps({'error': 'Task not found'})}\n\n"
                    break

                update = {
                    "status": current_task.status,
                    "progress": current_task.progress
                }
                yield f"id: {event_id}\ndata: {json.dumps(update)}\n\n"
                event_id += 1

                if current_task.status in ["completed", "failed", "cancelled"]:
                    final_task = db.get_task(task_id)
                    yield f"id: {event_id}\ndata: {json.dumps({'status': 'done', 'task': final_task.to_dict()})}\n\n"
                    break

                await asyncio.sleep(0.5)

        except Exception as e:
            yield f"id: {event_id}\ndata: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

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
        data = active_transcodes[task_id]
        # Signal cancellation to the FFmpeg process
        data["cancel"].set()
        # Cancel the background asyncio task
        bg_task = data.get("task")
        if bg_task and not bg_task.done():
            bg_task.cancel()
        db.update_task(task_id, status="cancelled")
        return {"message": "Task cancelled"}
    raise HTTPException(status_code=404, detail="Task not found or not running")
