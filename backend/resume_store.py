import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import DATABASE_PATH
from models import ResumeDetail, ResumeMeta


def _get_conn():
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id TEXT PRIMARY KEY,
            title TEXT,
            job_url TEXT,
            job_title TEXT,
            latex TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def create_resume(
    latex: str,
    *,
    title: Optional[str] = None,
    job_url: Optional[str] = None,
    job_title: Optional[str] = None,
) -> ResumeDetail:
    _init_db()
    rid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO resumes (id, title, job_url, job_title, latex, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
        (rid, title or "", job_url or "", job_title or "", latex, now, now),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM resumes WHERE id = ?", (rid,)).fetchone()
    conn.close()
    return _row_to_detail(row)


def get_resume(resume_id: str) -> Optional[ResumeDetail]:
    _init_db()
    conn = _get_conn()
    row = conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_detail(row)


def list_resumes() -> list[ResumeMeta]:
    _init_db()
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, title, job_url, job_title, created_at, updated_at FROM resumes ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return [_row_to_meta(r) for r in rows]


def update_resume(
    resume_id: str,
    *,
    title: Optional[str] = None,
    latex: Optional[str] = None,
) -> Optional[ResumeDetail]:
    _init_db()
    conn = _get_conn()
    row = conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()
    if not row:
        conn.close()
        return None
    updates = []
    args = []
    if title is not None:
        updates.append("title = ?")
        args.append(title)
    if latex is not None:
        updates.append("latex = ?")
        args.append(latex)
    if updates:
        updates.append("updated_at = ?")
        args.append(datetime.now(timezone.utc).isoformat())
        args.append(resume_id)
        conn.execute(f"UPDATE resumes SET {', '.join(updates)} WHERE id = ?", args)
        conn.commit()
    row = conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()
    conn.close()
    return _row_to_detail(row)


def delete_resume(resume_id: str) -> bool:
    _init_db()
    conn = _get_conn()
    cur = conn.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def _row_to_meta(r: sqlite3.Row) -> ResumeMeta:
    return ResumeMeta(
        id=r["id"],
        title=r["title"] or None,
        job_url=r["job_url"] or None,
        job_title=r["job_title"] or None,
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _row_to_detail(r: sqlite3.Row) -> ResumeDetail:
    return ResumeDetail(
        id=r["id"],
        title=r["title"] or None,
        job_url=r["job_url"] or None,
        job_title=r["job_title"] or None,
        latex=r["latex"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )
