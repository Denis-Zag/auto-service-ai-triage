import sqlite3
from pathlib import Path

from app.schemas import TriageRequest, TriageResponse


def initialize_database(database_path: Path) -> None:
    """Создаёт каталог и таблицу журнала, если их ещё нет."""

    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                client_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                text TEXT NOT NULL,
                category TEXT NOT NULL,
                confidence TEXT NOT NULL,
                escalate INTEGER NOT NULL,
                draft_reply TEXT NOT NULL,
                error TEXT
            )
            """
        )


def save_ticket(
    database_path: Path,
    request: TriageRequest,
    response: TriageResponse,
    error: str | None = None,
) -> int:
    """Сохраняет результат обработки и возвращает номер записи."""

    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO tickets (
                client_id, channel, text, category, confidence,
                escalate, draft_reply, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.client_id,
                request.channel.value,
                request.text,
                response.category.value,
                response.confidence.value,
                int(response.escalate),
                response.draft_reply,
                error,
            ),
        )
        return int(cursor.lastrowid)
