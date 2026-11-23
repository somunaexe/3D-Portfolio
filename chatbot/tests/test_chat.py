"""Tests for the chat layer (memory + condense-question) with a fake LLM and a real Redis."""
import sys
from pathlib import Path

import pytest
import redis

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import chat  # noqa: E402
import indexing  # noqa: E402
from fakes import DeadRedis, FakeLLM  # noqa: E402
from memory import ChatMemory  # noqa: E402
from retrieval import retrieve  # noqa: E402

BULWRITER = "Bulwriter — Collaborative Screenwriting Platform"


@pytest.fixture(scope="module")
def db_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("chroma")
    indexing.index_chunks(indexing.build_chunks(), db_dir=path)
    return path


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


# --- the command-line wrapper (chat.main) ---------------------------------------------------------

def _result(text, question="q?"):
    from query import Answer
    return chat.ChatResult(answer=Answer(answer=text, sources=[], retrieved=[]), standalone_question=question, history_turns=0)


def test_cli_says_which_model_it_is_using(monkeypatch, capsys):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:8b")
    monkeypatch.setattr(chat, "chat", lambda *a, **k: _result("Hello"))
    assert chat.main(["demo-chat-0123456789", "q?"]) == 0
    out = capsys.readouterr().out
    assert "(using ollama, model llama3.1:8b at http://localhost:11434)" in out and "Hello" in out


def test_cli_explains_an_empty_model_reply_instead_of_printing_nothing(monkeypatch, capsys):
    monkeypatch.setattr(chat, "chat", lambda *a, **k: _result("   \n"))
    assert chat.main(["demo-chat-0123456789", "q?"]) == 1
    assert "The model returned an empty answer." in capsys.readouterr().out


def test_cli_reports_a_failure_in_plain_words_with_a_hint(monkeypatch, capsys):
    def boom(*args, **kwargs):
        raise ConnectionError("Failed to connect to Ollama")
    monkeypatch.setattr(chat, "chat", boom)
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    assert chat.main(["demo-chat-0123456789", "q?"]) == 1
    out = capsys.readouterr().out
    assert "Could not get an answer: ConnectionError: Failed to connect to Ollama" in out
    assert "ollama list" in out and "Traceback" not in out


def test_cli_hint_for_openai_mentions_the_key_not_ollama(monkeypatch, capsys):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setattr(chat, "chat", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("401")))
    chat.main(["demo-chat-0123456789", "q?"])
    out = capsys.readouterr().out
    assert "OPENAI_API_KEY" in out and "ollama list" not in out


def test_cli_does_not_crash_on_characters_the_windows_console_cannot_show(monkeypatch):
    """A cp1252 console cannot encode an arrow; the CLI must print a replacement, not raise UnicodeEncodeError."""
    import io
    import sys
    raw = io.BytesIO()
    console = io.TextIOWrapper(raw, encoding="cp1252", errors="strict")
    monkeypatch.setattr(sys, "stdout", console)
    monkeypatch.setattr(chat, "chat", lambda *a, **k: _result("Python → Go"))
    assert chat.main(["demo-chat-0123456789", "q?"]) == 0
    console.flush()
    assert b"Python ? Go" in raw.getvalue()


def test_the_model_description_never_contains_the_api_key(monkeypatch):
    import llm
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "https://ollama.com")
    monkeypatch.setenv("OLLAMA_API_KEY", "placeholder-secret-value")
    assert "placeholder-secret-value" not in llm.describe_llm()


# --- the interactive mode (chat.repl) and the timeout hint ------------------------------------------

def _scripted_input(monkeypatch, lines):
    answers = iter(lines)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))


def test_repl_falls_back_to_in_process_memory_when_redis_is_not_running(monkeypatch, capsys):
    class NoRedis:
        def __init__(self):
            self.client = self

        def ping(self):
            raise redis.ConnectionError("refused")

    monkeypatch.setattr(chat, "ChatMemory", NoRedis)
    memory, note = chat.pick_memory()
    assert type(memory).__name__ == "InMemoryChatMemory" and "remembered only while this window stays open" in note


def test_repl_follow_ups_use_the_conversation_so_far_even_without_redis(monkeypatch, capsys):
    from memory import InMemoryChatMemory
    fake = FakeLLM(condensed="What technologies does Bulwriter use?")
    seen = []

    def fake_answer(question, llm=None, **options):
        seen.append(question)
        from query import Answer
        return Answer(answer="Built with Angular [1].", sources=[], retrieved=[])

    monkeypatch.setattr(chat, "get_llm", lambda: fake.runnable)
    monkeypatch.setattr(chat, "pick_memory", lambda: (InMemoryChatMemory(), None))
    monkeypatch.setattr(chat, "answer", fake_answer)
    _scripted_input(monkeypatch, ["Tell me about Bulwriter", "What technologies does it use?", "exit"])
    assert chat.repl() == 0
    assert seen == ["Tell me about Bulwriter", "What technologies does Bulwriter use?"]   # the 2nd was rewritten from history
    assert fake.kinds() == ["condense"]                                                    # first message: no condense call
    assert "(searched for: What technologies does Bulwriter use?)" in capsys.readouterr().out


def test_repl_rejects_empty_and_overlong_questions_and_keeps_going(monkeypatch, capsys):
    from memory import InMemoryChatMemory
    calls = []
    monkeypatch.setattr(chat, "get_llm", lambda: FakeLLM().runnable)
    monkeypatch.setattr(chat, "pick_memory", lambda: (InMemoryChatMemory(), None))
    monkeypatch.setattr(chat, "chat", lambda *a, **k: calls.append(a) or _result("ok"))
    _scripted_input(monkeypatch, ["", "   ", "x" * 201, "real question", "quit"])
    assert chat.repl() == 0
    assert len(calls) == 1 and "under 200 characters" in capsys.readouterr().out


def test_repl_ends_cleanly_on_ctrl_c_and_survives_a_model_error(monkeypatch, capsys):
    from memory import InMemoryChatMemory
    monkeypatch.setattr(chat, "get_llm", lambda: FakeLLM().runnable)
    monkeypatch.setattr(chat, "pick_memory", lambda: (InMemoryChatMemory(), None))
    state = {"n": 0}

    def flaky(*args, **kwargs):
        state["n"] += 1
        raise RuntimeError("model fell over")

    monkeypatch.setattr(chat, "chat", flaky)

    def inputs(prompt=""):
        if state["n"] == 0:
            return "hello"
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", inputs)
    assert chat.repl() == 0
    assert "Could not get an answer: RuntimeError: model fell over" in capsys.readouterr().out


def test_a_timeout_gets_a_hint_about_the_timeout_not_about_ollama_running():
    import httpx
    import llm
    hint = llm.troubleshooting_hint(httpx.ReadTimeout("timed out"))
    assert "LLM_TIMEOUT_SECONDS" in hint and "took too long" in hint


def test_the_cli_shows_the_timeout_hint(monkeypatch, capsys):
    import httpx
    monkeypatch.setattr(chat, "chat", lambda *a, **k: (_ for _ in ()).throw(httpx.ReadTimeout("timed out")))
    assert chat.main(["demo-chat-0123456789", "q?"]) == 1
    assert "LLM_TIMEOUT_SECONDS" in capsys.readouterr().out
