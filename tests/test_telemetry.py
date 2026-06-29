import pytest


def test_counting_client(monkeypatch):
    from tutorbench.llm.telemetry import CountingClient

    class FakeClient:
        def __init__(self):
            self.retry_count = 0

        def structured(self, **kwargs):
            # Simulate a retry on the first call
            if self.retry_count == 0:
                self.retry_count += 1
                raise Exception("Simulated retry")
            return {"result": "success"}

    fake_client = FakeClient()
    counting_client = CountingClient(fake_client)

    # Monkeypatch time.perf_counter to simulate deterministic durations
    times = [0.1, 0.2, 0.3, 0.4, 0.5]  # Simulated durations for calls
    call_index = 0

    def fake_perf_counter():
        nonlocal call_index
        if call_index < len(times):
            t = times[call_index]
            call_index += 1
            return t
        return times[-1]

    monkeypatch.setattr("time.perf_counter", fake_perf_counter)

    # Make structured calls and handle retries
    results = []
    for _ in range(5):
        try:
            result = counting_client.structured()
            results.append(result)
        except Exception as e:
            results.append(str(e))

    stats = counting_client.stats

    assert stats["n_calls"] == 5
    assert stats["n_errors"] == 1
    assert stats["retries"] == 1
    assert len(stats["durations"]) == 5
    assert stats["total_duration"] == pytest.approx(sum(stats["durations"]))
    # durations per call = end - start of consecutive perf_counter reads:
    # (0.2-0.1, 0.4-0.3, 0.5-0.5, 0.5-0.5, 0.5-0.5) -> [0.1, 0.1, 0, 0, 0]
    # p50 over sorted [0,0,0,0.1,0.1] -> 0 ; p95 -> 0.1*? interp near top
    assert stats["p50"] == pytest.approx(0.0)
    assert stats["p95"] == pytest.approx(0.1, abs=0.02)

def test_counting_client_retries(monkeypatch):
    from tutorbench.llm.telemetry import CountingClient

    class FakeClient:
        def __init__(self):
            self.retry_count = 0

        def structured(self, **kwargs):
            # Simulate a retry on the first call
            if self.retry_count < 2:
                self.retry_count += 1
                raise Exception("Simulated retry")
            return {"result": "success"}

    fake_client = FakeClient()
    counting_client = CountingClient(fake_client)

    # Monkeypatch time.perf_counter to simulate deterministic durations
    times = [0.1, 0.2, 0.3]  # Simulated durations for calls
    call_index = 0

    def fake_perf_counter():
        nonlocal call_index
        if call_index < len(times):
            t = times[call_index]
            call_index += 1
            return t
        return times[-1]

    monkeypatch.setattr("time.perf_counter", fake_perf_counter)

    # Make structured calls and handle retries
    results = []
    for _ in range(3):
        try:
            result = counting_client.structured()
            results.append(result)
        except Exception as e:
            results.append(str(e))

    stats = counting_client.stats

    assert stats["n_calls"] == 3
    
def test_counting_client_no_calls():
    from tutorbench.llm.telemetry import CountingClient

    class FakeClient:
        def structured(self, **kwargs):
            return {"result": "success"}

    fake_client = FakeClient()
    counting_client = CountingClient(fake_client)

    stats = counting_client.stats

    assert stats["n_calls"] == 0
    assert stats["retries"] == 0
    assert stats["p50"] is None
    assert stats["p95"] is None
