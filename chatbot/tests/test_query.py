"""Tests for the single-turn query pipeline, using a fake LLM (no Ollama or OpenAI needed).

The fake records the exact prompt it was handed and returns a scripted reply, so these
check everything AROUND the model: what retrieval puts in the prompt, how citations become
sources, and how the provider is chosen. They cannot judge the model's own answer quality.
"""
import sys
from pathlib import Path

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import indexing  # noqa: E402
import llm as llm_module  # noqa: E402
import query  # noqa: E402


@pytest.fixture(scope="module")
def db_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("chroma")
    indexing.index_chunks(indexing.build_chunks(), db_dir=path)
    return path


class FakeLLM:
    """A stand-in model: remembers the prompt it received, replies with a fixed string."""

    def __init__(self, reply):
        self.reply = reply
        self.prompts = []
        self.runnable = RunnableLambda(self._call)

    def _call(self, prompt_value):
        self.prompts.append(prompt_value.to_messages())
        return AIMessage(content=self.reply)


def ask(db_dir, question, reply="ok", **options):
    fake = FakeLLM(reply)
    result = query.answer(question, llm=fake.runnable, db_dir=db_dir, **options)
    return result, fake


def test_prompt_carries_the_rules_the_question_and_numbered_excerpts(db_dir):
    _, fake = ask(db_dir, "What did you do at Entain?", k=4)
    system, human = fake.prompts[0]
    assert "ONLY" in system.content and "Never guess or invent" in system.content
    assert "Question: What did you do at Entain?" in human.content
    for number in (1, 2, 3, 4):
        assert f"[{number}] " in human.content
    assert "[5] " not in human.content


def test_default_k_retrieves_ten_excerpts(db_dir):
    result, fake = ask(db_dir, "Have you used Docker?")
    assert len(result.retrieved) == 10
    assert "[10] " in fake.prompts[0][1].content


def test_more_excerpts_put_more_docker_chunks_in_front_of_the_llm(db_dir):
    """The reason for k=10: at k=3 the LLM only sees one of the chunks that mention Docker."""
    def docker_chunks(k):
        result, _ = ask(db_dir, "Have you used Docker?", k=k)
        return sum("docker" in chunk["text"].lower() for chunk in result.retrieved)

    assert docker_chunks(3) == 1
    assert docker_chunks(10) >= 2


def test_citations_become_sources_in_order_ignoring_duplicates_and_bad_numbers(db_dir):
    result, _ = ask(db_dir, "What did you do at Entain?", reply="They resolved complaints [2][1]. Also [2] and [99] and [0].", k=5)
    assert [s["id"] for s in result.sources] == [result.retrieved[1]["id"], result.retrieved[0]["id"]]
    assert set(result.sources[0]) == {"id", "title", "kind", "section", "links"}


def test_an_answer_with_no_citations_has_no_sources(db_dir):
    result, _ = ask(db_dir, "Do you like pizza?", reply="I don't have that information, please contact Somuna.")
    assert result.sources == []
    assert len(result.retrieved) == 10   # retrieval still ran; only the citations decide sources


def test_the_llm_reply_is_returned_as_the_answer_text(db_dir):
    result, _ = ask(db_dir, "Hello?", reply="Hi there")
    assert result.answer == "Hi there"


def test_unknown_provider_is_rejected(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "carrier-pigeon")
    with pytest.raises(ValueError, match="carrier-pigeon"):
        llm_module.get_llm()


@pytest.mark.parametrize(
    "provider, env, class_name",
    [
        ("ollama", {}, "ChatOllama"),
        ("openai", {"OPENAI_API_KEY": "sk-test-not-a-real-key"}, "ChatOpenAI"),
    ],
)
def test_provider_switch_builds_the_right_model_without_calling_it(monkeypatch, provider, env, class_name):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert type(llm_module.get_llm()).__name__ == class_name


def test_ollama_cloud_sends_the_api_key_as_a_bearer_token(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "https://ollama.com")
    monkeypatch.setenv("OLLAMA_MODEL", "example:model")
    monkeypatch.setenv("OLLAMA_API_KEY", "placeholder-not-a-real-key")
    client = llm_module.get_llm()._client._client           # built locally; no request is made
    assert str(client.base_url).rstrip("/") == "https://ollama.com"
    assert client.headers["authorization"] == "Bearer placeholder-not-a-real-key"


def test_a_local_ollama_server_gets_no_authorization_header(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    client = llm_module.get_llm()._client._client
    assert "authorization" not in client.headers
    assert "localhost:11434" in str(client.base_url)


# --- timeouts and the third-person rule -------------------------------------------------------------

def _client_timeout(monkeypatch, **env):
    for key in ("LLM_TIMEOUT_SECONDS", "OLLAMA_BASE_URL", "OLLAMA_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return llm_module.get_llm()._client._client.timeout.read


def test_a_local_ollama_model_gets_a_long_default_timeout_because_cpus_are_slow(monkeypatch):
    assert _client_timeout(monkeypatch) == 300.0
    assert _client_timeout(monkeypatch, OLLAMA_BASE_URL="http://127.0.0.1:11434") == 300.0


def test_a_hosted_ollama_keeps_the_short_default_timeout(monkeypatch):
    assert _client_timeout(monkeypatch, OLLAMA_BASE_URL="https://ollama.com", OLLAMA_API_KEY="placeholder") == 30.0


def test_the_timeout_can_always_be_overridden(monkeypatch):
    assert _client_timeout(monkeypatch, LLM_TIMEOUT_SECONDS="45") == 45.0


def test_the_prompt_forbids_speaking_as_somuna():
    rules = query.SYSTEM_PROMPT
    assert "You are NOT Somuna" in rules and "third person" in rules and 'Never use "I"' in rules
    assert "ONLY" in rules and "Never guess or invent" in rules   # the earlier rules are still there
