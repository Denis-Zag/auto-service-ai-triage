import sqlite3
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.schemas import Category, Confidence, TriageResponse


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """Не позволяет тестам создавать рабочую базу или вызывать модель."""

    monkeypatch.setenv("USE_LLM", "false")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "triage.db"))
    get_settings.cache_clear()


def test_health() -> None:
    """Служебная проверка подтверждает готовность приложения."""

    from app.main import app

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_triage_uses_fallback_and_saves_ticket(tmp_path, monkeypatch) -> None:
    """При отключённой модели результат эскалируется и сохраняется."""

    monkeypatch.setenv("USE_LLM", "false")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "triage.db"))
    get_settings.cache_clear()

    import importlib
    import app.main

    main = importlib.reload(app.main)
    with TestClient(main.app) as client:
        response = client.post(
            "/triage",
            json={
                "text": "После ремонта снова появился стук",
                "channel": "chat",
                "client_id": "test-client",
            },
        )

    assert response.status_code == 200
    assert response.json()["confidence"] == "low"
    assert response.json()["escalate"] is True
    assert "передано оператору" in response.json()["draft_reply"]
    with sqlite3.connect(main.settings.database_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    assert count == 1


def test_triage_rejects_empty_text() -> None:
    """Пустое обращение не проходит валидацию контракта."""

    from app.main import app

    with TestClient(app) as client:
        response = client.post(
            "/triage",
            json={"text": "", "channel": "chat", "client_id": "client"},
        )
    assert response.status_code == 422


def test_triage_rejects_whitespace_text() -> None:
    """Строка из пробелов считается пустым обращением."""

    from app.main import app

    with TestClient(app) as client:
        response = client.post(
            "/triage",
            json={"text": "   ", "channel": "chat", "client_id": "client"},
        )
    assert response.status_code == 422


def test_triage_returns_valid_llm_result(tmp_path, monkeypatch) -> None:
    """Корректный структурированный ответ модели проходит через API."""

    monkeypatch.setenv("USE_LLM", "true")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "triage.db"))
    get_settings.cache_clear()

    import importlib
    import app.main

    main = importlib.reload(app.main)
    expected = TriageResponse(
        category=Category.COMPLAINT,
        draft_reply="Передадим обращение мастеру для повторной проверки.",
        confidence=Confidence.HIGH,
        escalate=True,
    )
    monkeypatch.setattr(main, "triage_with_llm", AsyncMock(return_value=expected))

    with TestClient(main.app) as client:
        response = client.post(
            "/triage",
            json={
                "text": "После ремонта снова появился стук",
                "channel": "chat",
                "client_id": "prompt-test-client",
            },
        )

    assert response.status_code == 200
    assert response.json() == expected.model_dump(mode="json")
