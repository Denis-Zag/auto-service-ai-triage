import sqlite3
from typing import Any

from app.config import Settings
from app.schemas import TriageRequest, TriageResponse


def connect_database(settings: Settings) -> Any:
    """Открывает локальную SQLite или удалённую Turso по настройкам."""

    if settings.database_backend == "turso":
        if not settings.turso_database_url or not settings.turso_auth_token:
            raise RuntimeError(
                "Для DATABASE_BACKEND=turso нужны TURSO_DATABASE_URL "
                "и TURSO_AUTH_TOKEN"
            )

        import libsql

        return libsql.connect(
            database=settings.turso_database_url,
            auth_token=settings.turso_auth_token,
        )

    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(settings.database_path)


def initialize_database(settings: Settings) -> None:
    """Создаёт таблицу журнала в выбранном хранилище, если её ещё нет."""

    connection = connect_database(settings)
    try:
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
        connection.commit()
    finally:
        connection.close()


def save_ticket(
    settings: Settings,
    request: TriageRequest,
    response: TriageResponse,
    error: str | None = None,
) -> int:
    """Сохраняет результат обработки и возвращает номер записи."""

    connection = connect_database(settings)
    try:
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
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()
