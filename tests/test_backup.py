import sqlite3
from pathlib import Path

import pytest

from scripts.backup_turso import get_required_environment, verify_backup


def test_verify_backup_accepts_valid_database(tmp_path: Path) -> None:
    database_path = tmp_path / "backup.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE tickets (id INTEGER PRIMARY KEY)")
        connection.execute("INSERT INTO tickets DEFAULT VALUES")

    assert verify_backup(database_path) == 1


def test_verify_backup_rejects_database_without_tickets(tmp_path: Path) -> None:
    database_path = tmp_path / "backup.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE another_table (id INTEGER PRIMARY KEY)")

    with pytest.raises(RuntimeError, match="таблица tickets"):
        verify_backup(database_path)


def test_required_environment_rejects_empty_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TURSO_DATABASE_URL", "   ")

    with pytest.raises(RuntimeError, match="TURSO_DATABASE_URL"):
        get_required_environment("TURSO_DATABASE_URL")
