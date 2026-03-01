import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class JobStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guid TEXT UNIQUE,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    description TEXT,
                    link TEXT,
                    published TEXT,
                    match_score REAL DEFAULT 0,
                    missing_skills TEXT DEFAULT ''
                )
                """
            )
            conn.commit()
        logger.info("SQLite initialized at %s", self.db_path)

    def save_job(self, job: Dict[str, Any]) -> bool:
        with self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO jobs(guid, title, company, location, description, link, published, match_score, missing_skills)
                    VALUES(:guid, :title, :company, :location, :description, :link, :published, :match_score, :missing_skills)
                    """,
                    job,
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def recent_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
