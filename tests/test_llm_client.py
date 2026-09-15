import pytest
from pydantic import ValidationError

from app.llm_client import SYSTEM_PROMPT
from app.schemas import TriageResponse


def test_prompt_explains_category_boundaries() -> None:
    """Промпт явно разделяет повторную неисправность и обычную поддержку."""

    prompt = SYSTEM_PROMPT.lower()
    assert "повторная неисправность" in prompt
    assert "некачественной уже выполненной работе" in prompt
    assert "приоритет billing, затем complaint, затем support" in prompt


def test_response_rejects_unknown_category() -> None:
    """Неизвестная категория модели не проходит контракт."""

    with pytest.raises(ValidationError):
        TriageResponse.model_validate(
            {
                "category": "repair",
                "draft_reply": "Передадим обращение мастеру.",
                "confidence": "high",
                "escalate": True,
            }
        )


def test_response_rejects_more_than_six_sentences() -> None:
    """Слишком длинный черновик ответа не проходит контракт."""

    with pytest.raises(ValidationError):
        TriageResponse.model_validate(
            {
                "category": "support",
                "draft_reply": "Один. Два. Три. Четыре. Пять. Шесть. Семь.",
                "confidence": "high",
                "escalate": False,
            }
        )
