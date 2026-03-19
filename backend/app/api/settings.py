"""Settings API endpoints"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.models.settings import TranscodeSettings
from app.services.settings_service import settings_service
from app.services.scheduler import scheduler_service

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/")
async def get_settings():
    """Get current settings"""
    return settings_service.get_settings()


@router.post("/")
async def update_settings(settings: TranscodeSettings):
    """Update settings"""
    success = settings_service.save_settings(settings)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save settings")

    # Update scheduler if settings changed
    if settings.auto_scan_enabled:
        await scheduler_service.start()
    else:
        await scheduler_service.stop()

    return {"message": "Settings saved", "settings": settings.model_dump()}


@router.post("/scheduler/start")
async def start_scheduler():
    """Start the auto-scan scheduler"""
    settings = settings_service.load_settings()
    if not settings.auto_scan_enabled:
        raise HTTPException(status_code=400, detail="Auto-scan is not enabled in settings")

    await scheduler_service.start()
    return {"message": "Scheduler started"}


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the auto-scan scheduler"""
    await scheduler_service.stop()
    return {"message": "Scheduler stopped"}


@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status"""
    return scheduler_service.get_status()


@router.post("/scheduler/scan-now")
async def scan_now():
    """Trigger immediate scan"""
    settings = settings_service.load_settings()
    scheduler = scheduler_service

    # Run scan in background
    async def run_scan():
        await scheduler._scan_and_transcode(settings)

    import asyncio
    asyncio.create_task(run_scan())

    return {"message": "Scan started"}


@router.delete("/scan-history")
async def clear_scan_history():
    """Clear scan history"""
    settings_service.clear_scanned_history()
    return {"message": "Scan history cleared"}
