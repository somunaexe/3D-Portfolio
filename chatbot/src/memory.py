"""Conversation memory in Redis.

Schema (from the design doc): one key per conversation, `chat:<chat_id>`, whose value is a
JSON array of {"question": ..., "answer": ...} objects, oldest first. An array of objects
(not a dict keyed by question, not a delimiter-joined string) because a visitor can repeat a
question, and any delimiter can appear inside an answer.

Three safeguards:
  * chat_id comes from an untrusted visitor and becomes part of a Redis key, so it is validated;
  * appending is read-modify-write on one JSON value, so it runs under WATCH and retries if
    another request changed the key in between (otherwise concurrent turns lose each other);
  * history is bounded (last MAX_TURNS turns) and expires TTL_SECONDS after the last write.
"""
import json
import os
import re

import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
KEY_PREFIX = "chat:"
MAX_TURNS = 10
TTL_SECONDS = 24 * 60 * 60

CHAT_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")


def validate_chat_id(chat_id):
    if not isinstance(chat_id, str) or not CHAT_ID.fullmatch(chat_id):
        raise ValueError("chat_id must be 1-64 characters: letters, digits, '_' or '-'")
    return chat_id


class ChatMemory:
    def __init__(self, client=None, max_turns=MAX_TURNS, ttl_seconds=TTL_SECONDS):
        self.client = client or redis.Redis.from_url(REDIS_URL, decode_responses=True)
        self.max_turns = max_turns
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def key(chat_id):
        return f"{KEY_PREFIX}{validate_chat_id(chat_id)}"

    @staticmethod
    def _decode(raw):
        """Stored JSON -> list of turns. A corrupt or unexpected value counts as 'no history'."""
        if not raw:
            return []
        try:
            turns = json.loads(raw)
        except json.JSONDecodeError:
            return []
        return turns if isinstance(turns, list) else []

    def load(self, chat_id):
        return self._decode(self.client.get(self.key(chat_id)))

    def append(self, chat_id, question, answer):
        """Add one turn atomically; returns the stored history (trimmed to max_turns)."""
        key = self.key(chat_id)
        with self.client.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(key)                      # abort the write if `key` changes before EXEC
                    turns = self._decode(pipe.get(key))
                    turns.append({"question": question, "answer": answer})
                    turns = turns[-self.max_turns:]
                    pipe.multi()
                    pipe.set(key, json.dumps(turns), ex=self.ttl_seconds)
                    pipe.execute()
                    return turns
                except redis.WatchError:
                    continue                             # someone else wrote first: re-read and retry

    def clear(self, chat_id):
        self.client.delete(self.key(chat_id))
