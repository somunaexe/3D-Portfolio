"""Tests for the chat layer (memory + condense-question) with a fake LLM and a real Redis."""
import sys
from pathlib import Path

import pytest
import redis
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import chat  # noqa: E402
import indexing  # noqa: E402
from memory import ChatMemory  # noqa: E402
from retrieval import retrieve  # noqa: E402

BULWRITER = "Bulwriter — Collaborative Screenwriting Platform"


@pytest.fixture(scope="module")
def db_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("chroma")
    indexing.index_chunks(indexing.build_chunks(), db_dir=path)
    return path


class FakeLLM:
    """Replies to the condense step and the answer step separately, and records both."""

    def __init__(self, answer="They built it [1].", condensed="What technologies does Bulwriter use?"):
        self.answer, self.condensed = answer, condensed
        self.calls = []   # [("condense" | "answer", [system, human])]
        self.runnable = RunnableLambda(self._call)

    def _call(self, prompt_value):
        messages = prompt_value.to_messages()
        kind = "condense" if messages[0].content.startswith("Rewrite the visitor") else "answer"
        self.calls.append((kind, messages))
        return AIMessage(content=self.condensed if kind == "condense" else self.answer)

    def kinds(self):
        return [kind for kind, _ in self.calls]


def talk(db_dir, memory, fake, chat_id, question, **options):
    return chat.chat(chat_id, question, memory=memory, llm=fake.runnable, db_dir=db_dir, **options)


def test_the_first_message_skips_the_condense_call(db_dir, redis_client):
    fake = FakeLLM()
    result = talk(db_dir, ChatMemory(redis_client), fake, "c1", "Tell me about Bulwriter")
    assert fake.kinds() == ["answer"]                      # nothing to resolve, so no extra LLM call
    assert result.standalone_question == "Tell me about Bulwriter"
    assert result.history_turns == 0 and result.memory_error is None


def test_a_follow_up_is_condensed_then_answered(db_dir, redis_client):
    memory, fake = ChatMemory(redis_client), FakeLLM()
    talk(db_dir, memory, fake, "c1", "Tell me about Bulwriter")
    fake.calls.clear()
    result = talk(db_dir, memory, fake, "c1", "What technologies does it use?")
    assert fake.kinds() == ["condense", "answer"]
    assert result.standalone_question == "What technologies does Bulwriter use?"
    assert result.history_turns == 1
    # the answer step is asked the rewritten question, not the ambiguous one
    assert "Question: What technologies does Bulwriter use?" in fake.calls[1][1][1].content


def test_condensing_is_what_lets_retrieval_find_the_right_chunk(db_dir):
    """Why the step exists: 'it' carries no topic, so the raw follow-up retrieves the wrong chunks."""
    raw = [hit["title"] for hit in retrieve("What technologies does it use?", k=3, db_dir=db_dir)]
    standalone = [hit["title"] for hit in retrieve("What technologies does Bulwriter use?", k=3, db_dir=db_dir)]
    assert BULWRITER not in raw
    assert standalone[0] == BULWRITER


def test_retrieval_uses_the_standalone_question(db_dir, redis_client):
    memory, fake = ChatMemory(redis_client), FakeLLM()
    talk(db_dir, memory, fake, "c1", "Tell me about Bulwriter")
    result = talk(db_dir, memory, fake, "c1", "What technologies does it use?")
    assert result.answer.retrieved[0]["title"] == BULWRITER


def test_the_condense_prompt_sees_the_history_without_stale_citation_numbers(db_dir, redis_client):
    memory, fake = ChatMemory(redis_client), FakeLLM(answer="It is a screenwriting editor [3][7].")
    talk(db_dir, memory, fake, "c1", "Tell me about Bulwriter")
    talk(db_dir, memory, fake, "c1", "What technologies does it use?")
    condense_prompt = next(m for kind, m in fake.calls if kind == "condense")[1].content
    assert "Visitor: Tell me about Bulwriter" in condense_prompt
    assert "It is a screenwriting editor." in condense_prompt
    assert "[3]" not in condense_prompt and "[7]" not in condense_prompt
    assert "Latest message: What technologies does it use?" in condense_prompt


def test_memory_stores_what_the_visitor_typed_and_the_raw_answer(db_dir, redis_client):
    memory, fake = ChatMemory(redis_client), FakeLLM(answer="Built with Angular [2].")
    talk(db_dir, memory, fake, "c1", "Tell me about Bulwriter")
    talk(db_dir, memory, fake, "c1", "What technologies does it use?")
    assert memory.load("c1") == [
        {"question": "Tell me about Bulwriter", "answer": "Built with Angular [2]."},
        {"question": "What technologies does it use?", "answer": "Built with Angular [2]."},   # original wording, not the rewrite
    ]


def test_each_chat_only_sees_its_own_history(db_dir, redis_client):
    memory, fake = ChatMemory(redis_client), FakeLLM()
    talk(db_dir, memory, fake, "alice", "Tell me about Bulwriter")
    fake.calls.clear()
    result = talk(db_dir, memory, fake, "bob", "What technologies does it use?")
    assert result.history_turns == 0
    assert fake.kinds() == ["answer"]


@pytest.mark.parametrize("bad_rewrite", ["", "   ", '""', "x" * 600])
def test_an_unusable_rewrite_falls_back_to_the_visitors_own_words(db_dir, redis_client, bad_rewrite):
    memory, fake = ChatMemory(redis_client), FakeLLM(condensed=bad_rewrite)
    talk(db_dir, memory, fake, "c1", "Tell me about Bulwriter")
    result = talk(db_dir, memory, fake, "c1", "What technologies does it use?")
    assert result.standalone_question == "What technologies does it use?"


def test_quotes_around_the_rewrite_are_stripped(db_dir, redis_client):
    memory, fake = ChatMemory(redis_client), FakeLLM(condensed='"What technologies does Bulwriter use?"')
    talk(db_dir, memory, fake, "c1", "Tell me about Bulwriter")
    assert talk(db_dir, memory, fake, "c1", "and its stack?").standalone_question == "What technologies does Bulwriter use?"


def test_an_invalid_chat_id_is_rejected_before_any_llm_call(db_dir, redis_client):
    fake = FakeLLM()
    with pytest.raises(ValueError, match="chat_id"):
        talk(db_dir, ChatMemory(redis_client), fake, "bad id!", "hello")
    assert fake.calls == []


class DeadRedis:
    """Every operation fails like a Redis outage."""

    def get(self, *args, **kwargs):
        raise redis.ConnectionError("connection refused")

    def pipeline(self, *args, **kwargs):
        raise redis.ConnectionError("connection refused")


def test_the_visitor_still_gets_an_answer_when_redis_is_down(db_dir):
    fake = FakeLLM(answer="Somuna built Bulwriter [1].")
    result = talk(db_dir, ChatMemory(DeadRedis()), fake, "c1", "Tell me about Bulwriter")
    assert result.answer.answer == "Somuna built Bulwriter [1]."
    assert result.history_turns == 0
    assert "could not load history" in result.memory_error
    assert fake.kinds() == ["answer"]


def test_a_failed_save_is_reported_but_does_not_lose_the_answer(db_dir, redis_client):
    class SaveFails(ChatMemory):
        def append(self, *args, **kwargs):
            raise redis.ConnectionError("lost connection")

    result = talk(db_dir, SaveFails(redis_client), FakeLLM(), "c1", "Tell me about Bulwriter")
    assert result.answer.answer and "could not save" in result.memory_error


def test_long_assistant_replies_are_trimmed_in_the_condense_prompt():
    history = [{"question": "q", "answer": "word " * 500}]
    shown = chat.format_history(history)
    assert len(shown) < chat.ANSWER_CHARS_IN_HISTORY + 60 and shown.endswith("...")
