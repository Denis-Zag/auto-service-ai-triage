import json

import httpx

from app.config import Settings
from app.schemas import TriageRequest, TriageResponse


SYSTEM_PROMPT = """Ты — ассистент службы поддержки автосервиса.
Классифицируй обращение и подготовь краткий черновик ответа на русском языке.
Используй только факты из обращения и не придумывай цены, сроки или выполненные работы.

Выбери ровно одну категорию по этим правилам:
- billing: цены, оплата, предоплата, возврат денег или спорное списание;
- complaint: недовольство качеством ремонта или обслуживания, повторная неисправность
  после ремонта, претензия или требование исправить уже выполненную работу;
- support: вопрос о неисправности, диагностике, ремонте или записи, если клиент
  не сообщает о некачественной уже выполненной работе;
- other: обращение не подходит под три категории выше.

При пересечении правил используй приоритет billing, затем complaint, затем support.
Для спорного списания, возврата денег, претензии и повторной неисправности после
ремонта всегда устанавливай escalate=true.
Уверенность должна быть одной из: high, medium, low.
Если данных мало или ты сомневаешься, укажи confidence=low и escalate=true.
Верни только JSON с полями category, draft_reply, confidence, escalate.
Черновик ответа должен содержать от одного до шести предложений."""


async def triage_with_llm(
    request: TriageRequest,
    settings: Settings,
) -> TriageResponse:
    """Отправляет обращение в ProxyAPI и проверяет структуру ответа."""

    if not settings.proxyapi_key:
        raise RuntimeError("Переменная PROXYAPI_KEY не задана")

    payload = {
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request.text},
        ],
    }
    headers = {"Authorization": f"Bearer {settings.proxyapi_key}"}
    timeout = httpx.Timeout(settings.llm_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        api_response = await client.post(
            f"{settings.proxyapi_base_url}/chat/completions",
            json=payload,
            headers=headers,
        )
        api_response.raise_for_status()

    content = api_response.json()["choices"][0]["message"]["content"]
    return TriageResponse.model_validate(json.loads(content))
