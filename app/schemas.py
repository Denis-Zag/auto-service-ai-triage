from enum import StrEnum
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Channel(StrEnum):
    """Допустимые метки источника обращения."""

    EMAIL = "email"
    FORM = "form"
    CHAT = "chat"


class Category(StrEnum):
    """Категории обращений из контракта задания."""

    BILLING = "billing"
    SUPPORT = "support"
    COMPLAINT = "complaint"
    OTHER = "other"


class Confidence(StrEnum):
    """Уровень уверенности классификации."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TriageRequest(BaseModel):
    """Входные данные для обработки обращения."""

    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(min_length=1, max_length=2000)
    channel: Channel
    client_id: str = Field(min_length=1, max_length=100)


class TriageResponse(BaseModel):
    """Структурированный результат обработки обращения."""

    model_config = ConfigDict(str_strip_whitespace=True)

    category: Category
    draft_reply: str = Field(min_length=1)
    confidence: Confidence
    escalate: bool

    @field_validator("draft_reply")
    @classmethod
    def validate_sentence_count(cls, value: str) -> str:
        """Проверяет ограничение от одного до шести предложений."""

        parts = [part for part in re.split(r"[.!?]+(?:\s+|$)", value) if part.strip()]
        sentence_count = len(parts) or 1
        if sentence_count > 6:
            raise ValueError("draft_reply должен содержать не больше 6 предложений")
        return value
