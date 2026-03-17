from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import Settings


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_connection(settings: Settings) -> sqlite3.Connection:
    settings.ensure_paths()
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.execute("PRAGMA journal_mode = WAL;")
    return connection


def init_db(settings: Settings) -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection(settings) as connection:
        connection.executescript(schema)
        connection.commit()

