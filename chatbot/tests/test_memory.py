import json
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from memory import ChatMemory  # noqa: E402


def test_a_new_chat_has_no_history(redis_client):
    assert ChatMemory(redis_client).load("brand-new") == []


def test_turns_round_trip_oldest_first(redis_client):
    memory = ChatMemory(redis_client)
    memory.append("c1", "first?", "one")
    memory.append("c1", "second?", "two")
    assert memory.load("c1") == [{"question": "first?", "answer": "one"}, {"question": "second?", "answer": "two"}]


def test_the_stored_value_is_a_json_array_of_objects(redis_client):
    """The schema from the design doc: not a dict keyed by question, not a delimited string."""
    ChatMemory(redis_client).append("c1", "q", "a")
    assert json.loads(redis_client.get("chat:c1")) == [{"question": "q", "answer": "a"}]


def test_a_repeated_question_and_awkward_characters_survive(redis_client):
    """The two reasons a dict or delimiter format was rejected."""
    memory = ChatMemory(redis_client)
    memory.append("c1", "same question?", "first answer")
    memory.append("c1", "same question?", "second | answer with a ||| delimiter\nand a newline")
    turns = memory.load("c1")
    assert [t["answer"] for t in turns] == ["first answer", "second | answer with a ||| delimiter\nand a newline"]


def test_history_is_trimmed_to_the_most_recent_turns(redis_client):
    memory = ChatMemory(redis_client, max_turns=3)
    for number in range(1, 6):
        memory.append("c1", f"q{number}", f"a{number}")
    assert [t["question"] for t in memory.load("c1")] == ["q3", "q4", "q5"]


def test_history_expires_and_each_write_renews_the_expiry(redis_client):
    memory = ChatMemory(redis_client, ttl_seconds=100)
    memory.append("c1", "q", "a")
    assert 0 < redis_client.ttl("chat:c1") <= 100
    redis_client.expire("chat:c1", 5)
    memory.append("c1", "q2", "a2")
    assert redis_client.ttl("chat:c1") > 5


def test_conversations_are_isolated_from_each_other(redis_client):
    memory = ChatMemory(redis_client)
    memory.append("alice", "alice's question", "a")
    assert memory.load("bob") == []


def test_clear_forgets_a_conversation(redis_client):
    memory = ChatMemory(redis_client)
    memory.append("c1", "q", "a")
    memory.clear("c1")
    assert memory.load("c1") == []


@pytest.mark.parametrize("bad", ["", "has space", "a:b", "../etc/passwd", "x" * 65, "emoji-😀", "new\nline", None, 123])
def test_untrusted_chat_ids_are_rejected_before_touching_redis(redis_client, bad):
    memory = ChatMemory(redis_client)
    with pytest.raises(ValueError, match="chat_id"):
        memory.load(bad)
    with pytest.raises(ValueError, match="chat_id"):
        memory.append(bad, "q", "a")
    assert redis_client.keys("*") == []


@pytest.mark.parametrize("garbage", ["not json at all", '{"a": 1}', '"just a string"', "42"])
def test_a_corrupt_value_counts_as_no_history_and_heals_on_the_next_write(redis_client, garbage):
    redis_client.set("chat:c1", garbage)
    memory = ChatMemory(redis_client)
    assert memory.load("c1") == []
    memory.append("c1", "q", "a")
    assert memory.load("c1") == [{"question": "q", "answer": "a"}]


def test_concurrent_requests_on_one_chat_do_not_lose_turns(redis_client):
    """The read-modify-write race: without WATCH, simultaneous appends overwrite each other."""
    memory = ChatMemory(redis_client, max_turns=100)
    threads = [threading.Thread(target=memory.append, args=("shared", f"q{n}", f"a{n}")) for n in range(40)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    stored = {turn["question"] for turn in memory.load("shared")}
    assert stored == {f"q{n}" for n in range(40)}
