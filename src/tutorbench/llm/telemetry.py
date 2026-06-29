import math
import time


def _percentile(values: list[float], pct: float) -> float | None:
    """Linear-interpolation percentile (numpy default method). ``None`` when
    there is no sample."""
    if not values:
        return None
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    rank = (pct / 100) * (len(s) - 1)
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return s[lo]
    return s[lo] + (s[hi] - s[lo]) * (rank - lo)


class CountingClient:
    """Wraps an inner LLM client and records call counts, retries, and per-call
    wall-time, exposing p50/p95 latency via :attr:`stats`."""

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
            # A failed structured() call is one the caller retries, so the error
            # count is the retry count.
            "retries": self.errors,
            "durations": list(self.durations),
            "total_duration": sum(self.durations),
            "p50": _percentile(self.durations, 50),
            "p95": _percentile(self.durations, 95),
        }
