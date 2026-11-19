"""Small database helpers used by the Flask application."""

from pathlib import Path

from .database import get_db_connection


def get_user_by_email(database_path: str | Path, email: str):
    """Return a user row by email, or None when no account exists."""
    with get_db_connection(database_path) as connection:
        return connection.execute(
            "SELECT id, name, email, password_hash, created_at FROM users WHERE email = ?",
            (email,),
        ).fetchone()
