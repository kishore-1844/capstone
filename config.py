"""Application configuration."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"


class Config:
    SECRET_KEY = os.environ.get("TRELLO_SECRET_KEY", "dev-only-change-before-deploy")
    DATABASE_PATH = Path(os.environ.get("TRELLO_DATABASE_PATH", INSTANCE_DIR / "trello.db"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
