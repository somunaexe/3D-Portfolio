"""Test doubles shared by the chat and API tests."""
import redis
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda


class FakeLLM:
    """Replies to the condense step and the answer step separately, and records both.

    Pass error=Exception(...) to make every call fail like a provider outage."""

    def __init__(self, answer="They built it [1].", condensed="What technologies does Bulwriter use?", error=None):
        self.answer, self.condensed, self.error = answer, condensed, error
        self.calls = []   # [("condense" | "answer", [system, human])]
        self.runnable = RunnableLambda(self._call)

    def _call(self, prompt_value):
        if self.error is not None:
            raise self.error
        messages = prompt_value.to_messages()
        kind = "condense" if messages[0].content.startswith("Rewrite the visitor") else "answer"
        self.calls.append((kind, messages))
        return AIMessage(content=self.condensed if kind == "condense" else self.answer)

    def kinds(self):
        return [kind for kind, _ in self.calls]


class DeadRedis:
    """Every operation fails like a Redis outage."""

    def get(self, *args, **kwargs):
        raise redis.ConnectionError("connection refused")

    def pipeline(self, *args, **kwargs):
        raise redis.ConnectionError("connection refused")

    def zrangebyscore(self, *args, **kwargs):
        raise redis.ConnectionError("connection refused")
