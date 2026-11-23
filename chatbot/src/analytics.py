"""A short-lived log of what visitors ask and how the pipeline coped, for improving the chatbot.

WHAT IS STORED (per question): the question text with emails and phone numbers masked, the rewritten standalone
question, which CV chunks were retrieved and which were cited, how long it took, and whether it worked.
WHAT IS NOT STORED: the answer text, the chat id, the IP address, or anything else that identifies a visitor.
Entries are deleted after RETENTION_DAYS. The widget tells visitors this (see NOTICE in ChatWidget.jsx).

It is OFF unless ANALYTICS_ENABLED=true, so nothing is kept by accident (on a laptop, in tests, in a fork).
Logging must never break a chat: every failure here is swallowed and logged to the server log instead.

Storage: one Redis sorted set, `analytics:questions`, score = unix time, member = a JSON event. A sorted set
(not a list with a TTL) lets us drop entries individually once they are older than the retention window.
"""
import json
import logging
import os
import re
import time
import uuid

import redis

logger = logging.getLogger("chatbot.analytics")

KEY = "analytics:questions"
RETENTION_DAYS = int(os.environ.get("ANALYTICS_RETENTION_DAYS", "30"))
MAX_ENTRIES = 5000   # a hard ceiling, so a flood of traffic cannot fill Redis

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
LONG_NUMBER = re.compile(r"\+?\d[\d\s().-]{6,}\d")   # phone-like: 8+ digits with the usual separators


def enabled():
    return os.environ.get("ANALYTICS_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")


def mask_personal_details(text):
    """Visitors sometimes type their own email or phone number into the chat. Don't keep it."""
    return LONG_NUMBER.sub("[number]", EMAIL.sub("[email]", text))


def build_event(question, result=None, latency_ms=0, status="ok", now=None):
    """`result` is a chat.ChatResult (or None when the pipeline failed)."""
    event = {
        "id": uuid.uuid4().hex,
        "ts": int(now if now is not None else time.time()),
        "status": status,                                  # "ok" or "error"
        "question": mask_personal_details(question),
        "latency_ms": int(latency_ms),
    }
    if result is not None:
        retrieved = result.answer.retrieved
        cited = result.answer.sources
        event.update(
            standalone=mask_personal_details(result.standalone_question),
            had_history=result.history_turns > 0,
            retrieved=[chunk["id"] for chunk in retrieved],
            cited=[source["id"] for source in cited],
            cited_titles=[source["title"] for source in cited],
            supported=bool(cited),   # an answer that cites nothing is a guess or a "don't know": worth reviewing
        )
    return event


class QuestionLog:
    def __init__(self, client, retention_days=RETENTION_DAYS, max_entries=MAX_ENTRIES):
        self.client = client
        self.retention_seconds = retention_days * 86400
        self.max_entries = max_entries

    def record(self, event):
        """Never raises: a logging problem must not cost the visitor their answer."""
        try:
            pipe = self.client.pipeline()
            pipe.zadd(KEY, {json.dumps(event, ensure_ascii=False): event["ts"]})
            pipe.zremrangebyscore(KEY, 0, event["ts"] - self.retention_seconds)
            pipe.zremrangebyrank(KEY, 0, -self.max_entries - 1)   # keep only the newest max_entries
            pipe.expire(KEY, self.retention_seconds)
            pipe.execute()
        except (redis.RedisError, TypeError, ValueError) as error:
            logger.warning("could not record analytics event: %s", error)

    def events(self, days=None, now=None):
        """Events newest first, optionally only from the last `days` days."""
        now = now if now is not None else time.time()
        low = now - days * 86400 if days else 0
        raw = self.client.zrangebyscore(KEY, low, "+inf")
        events = []
        for item in raw:
            try:
                events.append(json.loads(item))
            except ValueError:
                continue   # a corrupt entry is skipped, not fatal
        return sorted(events, key=lambda e: e["ts"], reverse=True)
