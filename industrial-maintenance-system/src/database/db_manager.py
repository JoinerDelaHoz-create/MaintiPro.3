"""
Database Manager for Industrial CMMS using SQLite.
Handles connection, schema initialization, and transactional queries.
"""

from contextlib import contextmanager
import os
import sqlite3
from pathlib import Path
from typing import Generator, Optional


class DatabaseManager:
    """Manages SQLite database connection, tables initialization and queries."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Check for Vercel / Serverless environment (read-only filesystem)
            if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
                tmp_dir = Path("/tmp")
                tmp_dir.mkdir(parents=True, exist_ok=True)
                self.db_path = str(tmp_dir / "cmms.db")
                # If bundled data/cmms.db exists, copy it to /tmp if not already there
                base_dir = Path(__file__).resolve().parent.parent.parent
                bundled_db = base_dir / "data" / "cmms.db"
                if bundled_db.exists() and not Path(self.db_path).exists():
                    import shutil
                    try:
                        shutil.copyfile(str(bundled_db), self.db_path)
                    except Exception:
                        pass
            else:
                # Default to <project_root>/data/cmms.db
                base_dir = Path(__file__).resolve().parent.parent.parent
                data_dir = base_dir / "data"
                data_dir.mkdir(parents=True, exist_ok=True)
                self.db_path = str(data_dir / "cmms.db")
        else:
            self.db_path = db_path
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager providing an auto-closing SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initializes tables if they do not already exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Equipments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS equipments (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'OPERATIONAL',
                    operating_hours REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL
                );
            """)

            # 2. Work Orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS work_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_code TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    assigned_technician TEXT,
                    downtime_hours REAL DEFAULT 0.0,
                    cost REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    closed_at TEXT,
                    FOREIGN KEY (equipment_code) REFERENCES equipments (code) ON DELETE CASCADE
                );
            """)

            # 3. Telemetry Logs table (Arduino / IoT)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_code TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    vibration REAL NOT NULL,
                    current REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (equipment_code) REFERENCES equipments (code) ON DELETE CASCADE
                );
            """)

            # 4. Users table (RBAC: ADMIN vs TECHNICIAN)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('ADMIN', 'TECHNICIAN')),
                    created_at TEXT NOT NULL
                );
            """)

            conn.commit()


# Singleton / Global instance default
db_manager = DatabaseManager()

