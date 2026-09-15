from collections import defaultdict, deque
from time import monotonic


class ClientRateLimiter:
    """Ограничивает число запросов клиента за скользящую минуту."""

    def __init__(self, requests_per_minute: int) -> None:
        self.requests_per_minute = requests_per_minute
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, client_id: str) -> bool:
        """Возвращает True, если клиент ещё не исчерпал лимит."""

        now = monotonic()
        timestamps = self._requests[client_id]
        while timestamps and now - timestamps[0] >= 60:
            timestamps.popleft()
        if len(timestamps) >= self.requests_per_minute:
            return False
        timestamps.append(now)
        return True
