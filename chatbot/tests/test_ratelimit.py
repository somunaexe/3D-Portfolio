import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fakes import DeadRedis  # noqa: E402
from ratelimit import RateLimiter  # noqa: E402


class Clock:
    def __init__(self, now=1_000_000.0):
        self.now = now

    def __call__(self):
        return self.now


def test_requests_up_to_the_limit_are_allowed_and_the_next_is_refused(redis_client):
    limiter = RateLimiter(redis_client, limit=3, window_seconds=60, clock=Clock())
    assert [limiter.check("1.2.3.4")[0] for _ in range(3)] == [True, True, True]
    allowed, retry_after = limiter.check("1.2.3.4")
    assert allowed is False and 1 <= retry_after <= 60


def test_visitors_are_counted_separately(redis_client):
    limiter = RateLimiter(redis_client, limit=1, clock=Clock())
    assert limiter.check("alice")[0] and not limiter.check("alice")[0]
    assert limiter.check("bob")[0]


def test_a_new_window_starts_a_fresh_count(redis_client):
    clock = Clock()
    limiter = RateLimiter(redis_client, limit=1, window_seconds=60, clock=clock)
    assert limiter.check("a")[0] and not limiter.check("a")[0]
    clock.now += 60
    assert limiter.check("a")[0]


def test_retry_after_counts_down_to_the_end_of_the_window(redis_client):
    clock = Clock(now=60 * 1000 + 45)         # 45s into a window -> 15s left
    limiter = RateLimiter(redis_client, limit=1, window_seconds=60, clock=clock)
    limiter.check("a")
    assert limiter.check("a") == (False, 15)


def test_counter_keys_expire_so_redis_does_not_fill_up(redis_client):
    RateLimiter(redis_client, limit=5, window_seconds=60, clock=Clock()).check("a")
    (key,) = redis_client.keys("ratelimit:*")
    assert 0 < redis_client.ttl(key) <= 60


def test_it_fails_open_when_redis_is_down():
    assert RateLimiter(DeadRedis(), limit=1).check("a") == (True, 0)
