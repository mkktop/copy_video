"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.api import files, transcode, settings
from app.services.scheduler import scheduler_service

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings_service = settings.settings_service
    app_settings = settings_service.load_settings()

    # Start scheduler if enabled
    if app_settings.auto_scan_enabled:
        await scheduler_service.start()

    yield

    # Shutdown
    await scheduler_service.stop()


# Create FastAPI app
app = FastAPI(
    title="Copy Video",
    description="Video transcoding service with hash modification",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(files.router)
app.include_router(transcode.router)
app.include_router(settings.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "copy-video-backend"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Copy Video API",
        "docs": "/docs",
        "health": "/health"
    }


# Mount frontend static files (for production)
frontend_dist = Path("/app/frontend/dist")
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
