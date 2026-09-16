import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.config import PUBLIC_API_URL


# Luôn lưu database ngay tại thư mục gốc của project
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = str(BASE_DIR / "liscam.db")


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT NOT NULL UNIQUE,
            name TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id TEXT PRIMARY KEY,
            owner_token_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            provider_file_id TEXT,
            delete_reference TEXT,
            url TEXT,
            filename TEXT,
            mime_type TEXT,
            size INTEGER,
            width INTEGER,
            height INTEGER,
            duration REAL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,

            FOREIGN KEY (owner_token_id)
                REFERENCES api_tokens(id)
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_media_expires_at
        ON media(expires_at)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_media_owner
        ON media(owner_token_id)
    """)

    conn.commit()
    conn.close()


def create_token(name="liscam-app"):
    token = "lcs_" + secrets.token_urlsafe(32)

    conn = get_connection()

    cursor = conn.execute(
        """
        INSERT INTO api_tokens
        (token, name, active, created_at)
        VALUES (?, ?, 1, ?)
        """,
        (
            token,
            name,
            1,
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    conn.commit()

    token_id = cursor.lastrowid

    conn.close()

    return {
        "id": token_id,
        "token": token,
        "name": name,
    }


def get_token(token):
    if not token:
        return None

    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM api_tokens
        WHERE token = ?
        AND active = 1
        """,
        (token,),
    ).fetchone()

    conn.close()

    if row is None:
        return None

    return dict(row)


def verify_token(token):
    return get_token(token) is not None


def save_media(
    media_id,
    owner_token_id,
    provider,
    provider_file_id,
    delete_reference,
    url,
    filename,
    mime_type,
    size,
    width,
    height,
    duration,
    created_at,
    expires_at,
):
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO media (
            id,
            owner_token_id,
            provider,
            provider_file_id,
            delete_reference,
            url,
            filename,
            mime_type,
            size,
            width,
            height,
            duration,
            created_at,
            expires_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            media_id,
            owner_token_id,
            provider,
            provider_file_id,
            delete_reference,
            url,
            filename,
            mime_type,
            size,
            width,
            height,
            duration,
            created_at,
            expires_at,
        ),
    )

    conn.commit()
    conn.close()


def get_media(media_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM media
        WHERE id = ?
        """,
        (media_id,),
    ).fetchone()

    conn.close()

    if row is None:
        return None

    return dict(row)


def get_media_for_owner(media_id, owner_token_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM media
        WHERE id = ?
        AND owner_token_id = ?
        """,
        (media_id, owner_token_id),
    ).fetchone()

    conn.close()

    if row is None:
        return None

    return dict(row)


def delete_media(media_id):
    conn = get_connection()

    conn.execute(
        """
        DELETE FROM media
        WHERE id = ?
        """,
        (media_id,),
    )

    conn.commit()
    conn.close()


def delete_media_for_owner(media_id, owner_token_id):
    conn = get_connection()

    cursor = conn.execute(
        """
        DELETE FROM media
        WHERE id = ?
        AND owner_token_id = ?
        """,
        (media_id, owner_token_id),
    )

    conn.commit()

    deleted = cursor.rowcount > 0

    conn.close()

    return deleted


def get_expired_media():
    now = datetime.now(timezone.utc).isoformat()

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM media
        WHERE expires_at <= ?
        """,
        (now,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_public_api_url(path):
    return f"{PUBLIC_API_URL.rstrip('/')}/{path.lstrip('/')}"