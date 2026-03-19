"""Settings service for configuration persistence"""
import json
from pathlib import Path
from typing import Optional

from app.models.settings import TranscodeSettings
from app.config import DATA_DIR


class SettingsService:
    """Service for managing application settings"""

    def __init__(self):
        self.settings_file = DATA_DIR / "settings.json"
        self._settings: Optional[TranscodeSettings] = None

    def load_settings(self) -> TranscodeSettings:
        """Load settings from file, or create default"""
        if self._settings is not None:
            return self._settings

        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._settings = TranscodeSettings(**data)
                    return self._settings
            except Exception as e:
                print(f"Error loading settings: {e}, using defaults")

        # Return default settings
        self._settings = TranscodeSettings()
        return self._settings

    def save_settings(self, settings: TranscodeSettings) -> bool:
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings.model_dump(), f, indent=2, ensure_ascii=False)
            self._settings = settings
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def update_settings(self, **kwargs) -> TranscodeSettings:
        """Update specific settings and save"""
        current = self.load_settings()
        for key, value in kwargs.items():
            if hasattr(current, key):
                setattr(current, key, value)
        self.save_settings(current)
        return current

    def get_settings(self) -> dict:
        """Get settings as dict"""
        return self.load_settings().model_dump()

    def add_scanned_file(self, file_path: str):
        """Add a file to scan history"""
        settings = self.load_settings()
        if file_path not in settings.scanned_files:
            settings.scanned_files.append(file_path)
            self.save_settings(settings)

    def clear_scanned_history(self):
        """Clear scan history"""
        settings = self.load_settings()
        settings.scanned_files = []
        self.save_settings(settings)

    def is_file_scanned(self, file_path: str) -> bool:
        """Check if file was already scanned"""
        settings = self.load_settings()
        return file_path in settings.scanned_files


# Global settings service instance
settings_service = SettingsService()
