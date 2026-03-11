from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


def _row_factory(cursor: sqlite3.Cursor, row: tuple[Any, ...]) -> dict[str, Any]:
    return {column[0]: row[index] for index, column in enumerate(cursor.description)}


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = _row_factory
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    job_description TEXT,
                    job_link TEXT UNIQUE,
                    easy_apply INTEGER DEFAULT 0,
                    posted_date TEXT,
                    match_score REAL,
                    applied_status TEXT DEFAULT 'pending',
                    date_applied TEXT
                );

                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    resume_used TEXT,
                    cover_letter TEXT,
                    response_status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(job_id) REFERENCES jobs(id)
                );
                """
            )

    def upsert_job(self, job: dict[str, Any]) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO jobs (
                    job_title, company, location, job_description, job_link,
                    easy_apply, posted_date, match_score, applied_status, date_applied
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_link) DO UPDATE SET
                    job_title=excluded.job_title,
                    company=excluded.company,
                    location=excluded.location,
                    job_description=excluded.job_description,
                    easy_apply=excluded.easy_apply,
                    posted_date=excluded.posted_date,
                    match_score=COALESCE(excluded.match_score, jobs.match_score),
                    applied_status=COALESCE(jobs.applied_status, excluded.applied_status),
                    date_applied=COALESCE(jobs.date_applied, excluded.date_applied)
                """,
                (
                    job["job_title"],
                    job["company"],
                    job.get("location"),
                    job.get("job_description"),
                    job["job_link"],
                    int(bool(job.get("easy_apply"))),
                    job.get("posted_date"),
                    job.get("match_score"),
                    job.get("applied_status", "pending"),
                    job.get("date_applied"),
                ),
            )
            if cursor.lastrowid:
                return int(cursor.lastrowid)
            job_row = connection.execute(
                "SELECT id FROM jobs WHERE job_link = ?",
                (job["job_link"],),
            ).fetchone()
            return int(job_row["id"])

    def create_application(self, job_id: int, resume_used: str, cover_letter: str | None) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO applications (job_id, resume_used, cover_letter)
                VALUES (?, ?, ?)
                """,
                (job_id, resume_used, cover_letter),
            )

    def mark_applied(self, job_link: str) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE jobs
                SET applied_status = 'applied',
                    date_applied = CURRENT_TIMESTAMP
                WHERE job_link = ?
                """,
                (job_link,),
            )

    def mark_reviewed(self, job_link: str) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE jobs
                SET applied_status = 'reviewed'
                WHERE job_link = ?
                """,
                (job_link,),
            )

    def jobs_applied_today(self) -> int:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM jobs
                WHERE applied_status = 'applied'
                  AND date(date_applied) = date('now', 'localtime')
                """
            ).fetchone()
            return int(row["total"])

    def dashboard_metrics(self) -> dict[str, Any]:
        with self.connect() as connection:
            summary = connection.execute(
                """
                SELECT
                    COUNT(*) AS total_jobs,
                    SUM(CASE WHEN applied_status = 'applied' THEN 1 ELSE 0 END) AS applied_jobs,
                    AVG(match_score) AS average_match_score
                FROM jobs
                """
            ).fetchone()
            companies = connection.execute(
                """
                SELECT company, COUNT(*) AS total
                FROM jobs
                WHERE applied_status = 'applied'
                GROUP BY company
                ORDER BY total DESC, company ASC
                LIMIT 10
                """
            ).fetchall()
            recent_jobs = connection.execute(
                """
                SELECT job_title, company, location, match_score, applied_status, job_link
                FROM jobs
                ORDER BY COALESCE(match_score, 0) DESC, id DESC
                LIMIT 25
                """
            ).fetchall()
            return {
                "summary": summary,
                "companies": companies,
                "recent_jobs": recent_jobs,
            }

    def export_snapshot(self, export_path: Path) -> Path:
        with self.connect() as connection:
            jobs = connection.execute(
                """
                SELECT id, job_title, company, location, job_description, job_link,
                       easy_apply, posted_date, match_score, applied_status, date_applied
                FROM jobs
                ORDER BY id ASC
                """
            ).fetchall()
            applications = connection.execute(
                """
                SELECT id, job_id, resume_used, cover_letter, response_status, created_at
                FROM applications
                ORDER BY id ASC
                """
            ).fetchall()

        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_text(
            json.dumps({"jobs": jobs, "applications": applications}, indent=2),
            encoding="utf-8",
        )
        return export_path

    def import_snapshot(self, payload: bytes) -> None:
        data = json.loads(payload.decode("utf-8"))
        jobs = data.get("jobs", [])
        applications = data.get("applications", [])
        job_id_map: dict[int, int] = {}

        for job in jobs:
            normalized_job = {
                "job_title": job["job_title"],
                "company": job["company"],
                "location": job.get("location"),
                "job_description": job.get("job_description"),
                "job_link": job["job_link"],
                "easy_apply": job.get("easy_apply"),
                "posted_date": job.get("posted_date"),
                "match_score": job.get("match_score"),
                "applied_status": job.get("applied_status", "pending"),
                "date_applied": job.get("date_applied"),
            }
            new_job_id = self.upsert_job(normalized_job)
            if normalized_job["applied_status"] == "applied":
                self.mark_applied(normalized_job["job_link"])
            elif normalized_job["applied_status"] == "reviewed":
                self.mark_reviewed(normalized_job["job_link"])
            old_id = int(job.get("id", new_job_id))
            job_id_map[old_id] = new_job_id

        with self.connect() as connection:
            for application in applications:
                mapped_job_id = job_id_map.get(int(application["job_id"]))
                if mapped_job_id is None:
                    continue
                exists = connection.execute(
                    """
                    SELECT 1
                    FROM applications
                    WHERE job_id = ? AND COALESCE(resume_used, '') = COALESCE(?, '')
                    """,
                    (mapped_job_id, application.get("resume_used")),
                ).fetchone()
                if exists:
                    continue
                connection.execute(
                    """
                    INSERT INTO applications (
                        job_id, resume_used, cover_letter, response_status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        mapped_job_id,
                        application.get("resume_used"),
                        application.get("cover_letter"),
                        application.get("response_status", "pending"),
                        application.get("created_at"),
                    ),
                )
