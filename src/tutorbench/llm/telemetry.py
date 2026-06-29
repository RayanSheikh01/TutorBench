import time


class CountingClient:
    """Wraps an inner LLM client and records call counts, errors, and durations."""

    def __init__(self, inner):
        self.inner = inner
        self.count = 0
        self.errors = 0
        self.durations: list[float] = []

    def structured(self, **kwargs):
        self.count += 1
        start = time.perf_counter()
        try:
            return self.inner.structured(**kwargs)
        except Exception:
            self.errors += 1
            raise
        finally:
            self.durations.append(time.perf_counter() - start)

    @property
    def stats(self) -> dict:
        return {
            "n_calls": self.count,
            "n_errors": self.errors,
            "durations": list(self.durations),
            "total_duration": sum(self.durations),
        }
