"""Database connection and models"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from contextlib import contextmanager

from app.config import DATABASE_URL, DATA_DIR


class Task:
    """Transcode task model"""
    def __init__(self, id: Optional[int], input_path: str, output_path: str,
                 status: str, progress: float = 0, error: Optional[str] = None,
                 created_at: Optional[str] = None, completed_at: Optional[str] = None,
                 metadata: Optional[str] = None):
        self.id = id
        self.input_path = input_path
        self.output_path = output_path
        self.status = status  # pending, processing, completed, failed
        self.progress = progress
        self.error = error
        self.created_at = created_at or datetime.now().isoformat()
        self.completed_at = completed_at
        self.metadata = metadata  # JSON string of metadata config

    def to_dict(self):
        result = {
            "id": self.id,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "status": self.status,
            "progress": self.progress,
            "error": self.error,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }
        if self.metadata:
            try:
                result["metadata"] = json.loads(self.metadata)
            except:
                result["metadata"] = {}
        return result


class Database:
    """Database manager"""

    def __init__(self):
        db_path = DATA_DIR / "copy_video.db"
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_tables()

    def _init_tables(self):
        """Initialize database tables"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_path TEXT NOT NULL,
                output_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                progress REAL DEFAULT 0,
                error TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                metadata TEXT
            )
        """)
        self.conn.commit()

    def create_task(self, input_path: str, output_path: str, metadata: Optional[dict] = None) -> Task:
        """Create a new task"""
        cursor = self.conn.cursor()
        metadata_json = json.dumps(metadata) if metadata else None
        cursor.execute(
            "INSERT INTO tasks (input_path, output_path, status, created_at, metadata) VALUES (?, ?, 'pending', ?, ?)",
            (input_path, output_path, datetime.now().isoformat(), metadata_json)
        )
        self.conn.commit()
        return Task(cursor.lastrowid, input_path, output_path, "pending", metadata=metadata_json)

    def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row:
            return Task(*row)
        return None

    def update_task(self, task_id: int, **kwargs):
        """Update task fields"""
        valid_fields = {"status", "progress", "error", "completed_at"}
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        if not updates:
            return

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [task_id]

        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        self.conn.commit()

    def get_all_tasks(self, limit: int = 100) -> List[Task]:
        """Get all tasks, ordered by creation time"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [Task(*row) for row in rows]


# Global database instance
db = Database()
