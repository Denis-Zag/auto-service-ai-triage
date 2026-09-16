import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.config import Settings
from app.database import initialize_database, save_ticket
from app.schemas import (
    Category,
    Channel,
    Confidence,
    TriageRequest,
    TriageResponse,
)


def turso_settings() -> Settings:
    """Возвращает тестовые настройки удалённой базы без настоящих секретов."""

    return Settings(
        database_backend="turso",
        turso_database_url="libsql://example.turso.io",
        turso_auth_token="test-token",
    )


def test_turso_requires_both_credentials() -> None:
    """Облачный режим не запускается с неполной конфигурацией."""

    settings = Settings(
        database_backend="turso",
        turso_database_url="libsql://example.turso.io",
        turso_auth_token=None,
    )

    with pytest.raises(RuntimeError, match="TURSO_AUTH_TOKEN"):
        initialize_database(settings)


def test_initialize_database_uses_turso_credentials(monkeypatch) -> None:
    """Инициализация передаёт URL и токен официальному клиенту Turso."""

    connection = MagicMock()
    connect = MagicMock(return_value=connection)
    monkeypatch.setitem(sys.modules, "libsql", SimpleNamespace(connect=connect))

    initialize_database(turso_settings())

    connect.assert_called_once_with(
        database="libsql://example.turso.io",
        auth_token="test-token",
    )
    connection.execute.assert_called_once()
    connection.commit.assert_called_once()
    connection.close.assert_called_once()


def test_save_ticket_returns_remote_row_id(monkeypatch) -> None:
    """Запись в Turso использует тот же контракт, что и локальная SQLite."""

    cursor = MagicMock(lastrowid=42)
    connection = MagicMock()
    connection.execute.return_value = cursor
    monkeypatch.setitem(
        sys.modules,
        "libsql",
        SimpleNamespace(connect=MagicMock(return_value=connection)),
    )
    request = TriageRequest(
        text="После ремонта снова появился стук",
        channel=Channel.CHAT,
        client_id="cloud-test",
    )
    response = TriageResponse(
        category=Category.COMPLAINT,
        draft_reply="Передадим обращение мастеру.",
        confidence=Confidence.HIGH,
        escalate=True,
    )

    ticket_id = save_ticket(turso_settings(), request, response)

    assert ticket_id == 42
    connection.commit.assert_called_once()
    connection.close.assert_called_once()
