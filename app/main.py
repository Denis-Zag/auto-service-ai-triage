import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from app.config import get_settings
from app.database import initialize_database, save_ticket
from app.llm_client import triage_with_llm
from app.rate_limiter import ClientRateLimiter
from app.schemas import Category, Confidence, TriageRequest, TriageResponse


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()
rate_limiter = ClientRateLimiter(settings.requests_per_minute)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Подготавливает выбранное хранилище перед запуском API."""

    initialize_database(settings)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)


def fallback_response() -> TriageResponse:
    """Возвращает безопасный ответ при недоступности модели."""

    return TriageResponse(
        category=Category.OTHER,
        draft_reply=(
            "Ваше обращение передано оператору автосервиса. "
            "Оператор уточнит информацию и свяжется с вами."
        ),
        confidence=Confidence.LOW,
        escalate=True,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    """Подтверждает, что приложение запущено."""

    return {"status": "ok"}


@app.post("/triage", response_model=TriageResponse)
async def triage(request: TriageRequest) -> TriageResponse:
    """Классифицирует обращение и сохраняет результат в журнале."""

    if not rate_limiter.is_allowed(request.client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Превышен лимит запросов для client_id",
        )

    logger.info(
        "Обработка обращения: client_id=%s channel=%s text_length=%d",
        request.client_id,
        request.channel.value,
        len(request.text),
    )
    error_name = None
    try:
        if not settings.use_llm:
            raise RuntimeError("LLM отключена настройкой USE_LLM")
        response = await triage_with_llm(request, settings)
    except Exception as error:
        error_name = type(error).__name__
        logger.exception("Ошибка LLM: error_type=%s", error_name)
        response = fallback_response()

    ticket_id = save_ticket(settings, request, response, error_name)
    logger.info("Обращение сохранено: ticket_id=%d", ticket_id)
    return response
