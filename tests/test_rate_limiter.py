import app.rate_limiter as rate_limiter_module
from app.rate_limiter import ClientRateLimiter


def test_rate_limiter_blocks_excess_request() -> None:
    """Лишний запрос одного клиента блокируется в пределах минуты."""

    limiter = ClientRateLimiter(requests_per_minute=2)

    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is False


def test_rate_limiter_allows_request_after_minute(monkeypatch) -> None:
    """После окончания минутного окна клиент снова может отправить запрос."""

    moments = iter([0.0, 10.0, 61.0])
    monkeypatch.setattr(rate_limiter_module, "monotonic", lambda: next(moments))
    limiter = ClientRateLimiter(requests_per_minute=1)

    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is False
    assert limiter.is_allowed("client-1") is True
