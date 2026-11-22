"""Per-visitor rate limiting, kept in Redis so the limit holds across server instances.

Every /chat call costs one or two LLM requests, so an unauthenticated public endpoint needs a
cap. Fixed window: count requests per (identifier, minute) with INCR and let the key expire.
A visitor can burst up to 2x the limit across a window boundary; that is fine for cost control.

Fails OPEN: if Redis is unreachable the request is allowed, because a Redis blip should not take
the whole chatbot down. (The trade-off: during an outage nothing is limited.)
"""
import logging
import time

import redis

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, client, limit=20, window_seconds=60, clock=time.time, prefix="ratelimit:"):
        self.client = client
        self.limit = limit
        self.window_seconds = window_seconds
        self.clock = clock
        self.prefix = prefix

    def check(self, identifier):
        """Count this request. Returns (allowed, retry_after_seconds)."""
        now = self.clock()
        window = int(now // self.window_seconds)
        key = f"{self.prefix}{identifier}:{window}"
        try:
            with self.client.pipeline() as pipe:
                pipe.incr(key)
                pipe.expire(key, self.window_seconds)
                count, _ = pipe.execute()
        except redis.RedisError:
            logger.warning("rate limiter could not reach Redis; allowing the request")
            return True, 0
        if count > self.limit:
            return False, max(1, int(self.window_seconds - (now % self.window_seconds)))
        return True, 0
