"""HTTP-level tests: real FastAPI app, real Redis, fake LLM, throwaway Chroma index."""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import api  # noqa: E402
import indexing  # noqa: E402
from fakes import DeadRedis, FakeLLM  # noqa: E402
from memory import ChatMemory  # noqa: E402
from ratelimit import RateLimiter  # noqa: E402

CHAT_ID = "visitor-0123456789abcdef"
ORIGIN = "https://somunaexe.github.io"
SHAPE = {"answer", "sources", "error"}


@pytest.fixture(scope="module")
def db_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("chroma")
    indexing.index_chunks(indexing.build_chunks(), db_dir=path)
    return path


@pytest.fixture
def make_client(db_dir, redis_client):
    def build(llm=None, memory=None, limit=1000, trust_x_real_ip=False):
        fake = llm or FakeLLM()
        app = api.create_app(allowed_origins=[ORIGIN], trust_x_real_ip=trust_x_real_ip)
        app.dependency_overrides[api.get_memory] = lambda: memory or ChatMemory(redis_client)
        app.dependency_overrides[api.get_chat_llm] = lambda: fake.runnable
        app.dependency_overrides[api.get_limiter] = lambda: RateLimiter(redis_client, limit=limit)
        app.dependency_overrides[api.get_chat_options] = lambda: {"db_dir": db_dir}
        return TestClient(app), fake

    return build


def post(client, **body):
    payload = {"chat_id": CHAT_ID, "question": "What did you do at Entain?", **body}
    return client.post("/chat", json=payload)


def test_a_good_request_returns_the_contract_shape(make_client):
    client, _ = make_client(FakeLLM(answer="They managed customer service [1]."))
    response = post(client)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == SHAPE
    assert body["answer"] == "They managed customer service [1]."
    assert body["error"] is None
    assert isinstance(body["sources"], list) and all(isinstance(s, str) for s in body["sources"])


def test_sources_are_readable_section_labels(make_client):
    client, _ = make_client(FakeLLM(answer="Cited [1][2][1]."))
    sources = post(client, question="What did you do at Entain?").json()["sources"]
    assert sources[0] == "Experience: Customer Service Manager at Entain"
    assert len(sources) == len(set(sources)) == 2   # the duplicate [1] collapses


@pytest.mark.parametrize(
    "source, label",
    [
        ({"section": "Projects", "title": "Uber Clone"}, "Projects: Uber Clone"),
        ({"section": "Education", "title": "Education"}, "Education"),
        ({"section": "Key Skills", "title": "Key Skills"}, "Key Skills"),
        ({"section": None, "title": "Contact & headline"}, "Contact & headline"),
        ({"title": "Contact & headline"}, "Contact & headline"),
    ],
)
def test_source_label_formats(source, label):
    assert api.source_label(source) == label


def test_an_answer_that_cites_nothing_has_an_empty_sources_list(make_client):
    client, _ = make_client(FakeLLM(answer="I don't have that information."))
    assert post(client).json() == {"answer": "I don't have that information.", "sources": [], "error": None}


def test_the_conversation_carries_over_between_requests(make_client):
    client, fake = make_client()
    post(client, question="Tell me about Bulwriter")
    fake.calls.clear()
    post(client, question="What technologies does it use?")
    assert fake.kinds() == ["condense", "answer"]


def test_different_chat_ids_do_not_share_history(make_client):
    client, fake = make_client()
    post(client, question="Tell me about Bulwriter")
    fake.calls.clear()
    post(client, chat_id="someone-else-0123456789", question="What technologies does it use?")
    assert fake.kinds() == ["answer"]


# --- input validation: every failure keeps the {answer, sources, error} shape ---------------------

BAD_REQUESTS = [
    ("missing question", {"chat_id": CHAT_ID}, "question"),
    ("missing chat_id", {"question": "hi"}, "chat_id"),
    ("empty question", {"chat_id": CHAT_ID, "question": ""}, "question"),
    ("blank question", {"chat_id": CHAT_ID, "question": "   \n\t "}, "question"),
    ("201 characters", {"chat_id": CHAT_ID, "question": "x" * 201}, "question"),
    ("wrong type", {"chat_id": CHAT_ID, "question": 42}, "question"),
    ("chat_id too short", {"chat_id": "short", "question": "hi"}, "chat_id"),
    ("chat_id too long", {"chat_id": "a" * 65, "question": "hi"}, "chat_id"),
    ("chat_id with a colon", {"chat_id": "visitor:0123456789abcdef", "question": "hi"}, "chat_id"),
    ("chat_id path trick", {"chat_id": "../../etc/passwd-padding", "question": "hi"}, "chat_id"),
    ("unknown field", {"chat_id": CHAT_ID, "question": "hi", "message": "typo"}, "message"),
]


@pytest.mark.parametrize("label, body, field", BAD_REQUESTS, ids=[b[0] for b in BAD_REQUESTS])
def test_invalid_requests_get_422_in_the_contract_shape(make_client, label, body, field):
    client, fake = make_client()
    response = client.post("/chat", json=body)
    assert response.status_code == 422
    payload = response.json()
    assert set(payload) == SHAPE and payload["answer"] is None and payload["sources"] == []
    assert payload["error"].startswith("Invalid request:") and field in payload["error"]
    assert fake.calls == []                                   # rejected before any LLM cost


def test_a_question_of_exactly_200_characters_is_accepted(make_client):
    client, _ = make_client()
    assert post(client, question="x" * 200).status_code == 200


def test_surrounding_whitespace_does_not_count_toward_the_limit(make_client):
    client, _ = make_client()
    assert post(client, question="  " + "x" * 200 + "  ").status_code == 200


def test_the_error_message_never_echoes_the_visitors_input(make_client):
    client, _ = make_client()
    secret = "my-password-is-hunter2 " * 20
    assert "hunter2" not in client.post("/chat", json={"chat_id": CHAT_ID, "question": secret}).text


def test_a_non_json_body_is_rejected_in_the_same_shape(make_client):
    client, _ = make_client()
    response = client.post("/chat", content="not json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422 and set(response.json()) == SHAPE


@pytest.mark.parametrize("method, path, status", [("GET", "/chat", 405), ("GET", "/nope", 404)])
def test_routing_errors_also_use_the_contract_shape(make_client, method, path, status):
    client, _ = make_client()
    response = client.request(method, path)
    assert response.status_code == status and set(response.json()) == SHAPE and response.json()["error"]


# --- rate limiting ------------------------------------------------------------------------------

def test_requests_over_the_limit_get_429_with_retry_after(make_client):
    client, fake = make_client(limit=2)
    assert [post(client).status_code for _ in range(2)] == [200, 200]
    calls_before = len(fake.calls)
    response = post(client)
    assert response.status_code == 429
    assert set(response.json()) == SHAPE and "Too many requests" in response.json()["error"]
    assert 1 <= int(response.headers["Retry-After"]) <= 60
    assert len(fake.calls) == calls_before                    # a limited request costs nothing


def test_a_fake_x_real_ip_cannot_dodge_the_limit_unless_the_header_is_trusted(make_client):
    """Default: the header is ignored, so rotating it does not give a visitor a fresh allowance."""
    client, _ = make_client(limit=2)
    codes = [client.post("/chat", json={"chat_id": CHAT_ID, "question": "hi"}, headers={"X-Real-IP": f"203.0.113.{n}"}).status_code for n in range(4)]
    assert codes == [200, 200, 429, 429]


def test_behind_a_trusted_proxy_each_visitor_gets_their_own_allowance(make_client):
    client, _ = make_client(limit=1, trust_x_real_ip=True)
    send = lambda ip: client.post("/chat", json={"chat_id": CHAT_ID, "question": "hi"}, headers={"X-Real-IP": ip}).status_code
    assert [send("203.0.113.1"), send("203.0.113.2"), send("203.0.113.1")] == [200, 200, 429]


@pytest.mark.parametrize("bad", ["", "not-an-ip", "1.2.3.4, 5.6.7.8", "<script>"])
def test_a_missing_or_invalid_x_real_ip_falls_back_to_the_socket_address(make_client, bad):
    client, _ = make_client(limit=1, trust_x_real_ip=True)
    send = lambda: client.post("/chat", json={"chat_id": CHAT_ID, "question": "hi"}, headers={"X-Real-IP": bad}).status_code
    assert [send(), send()] == [200, 429]      # both counted against the same (socket) address


# --- failures downstream ------------------------------------------------------------------------

def test_an_llm_outage_returns_503_without_leaking_details(make_client):
    secret = "ConnectError to http://internal-host:11434 using key sk-live-SECRET123"
    client, _ = make_client(FakeLLM(error=RuntimeError(secret)))
    response = post(client)
    assert response.status_code == 503
    assert set(response.json()) == SHAPE and response.json()["answer"] is None
    assert "SECRET123" not in response.text and "internal-host" not in response.text


def test_when_redis_is_down_the_visitor_still_gets_an_answer(make_client):
    client, _ = make_client(FakeLLM(answer="Built Bulwriter [1]."), memory=ChatMemory(DeadRedis()))
    response = post(client, question="Tell me about Bulwriter")
    assert response.status_code == 200
    assert response.json()["answer"] == "Built Bulwriter [1]." and response.json()["error"] is None
    assert response.headers["X-Chat-Memory"] == "unavailable"


def test_the_memory_header_is_absent_when_memory_works(make_client):
    client, _ = make_client()
    assert "X-Chat-Memory" not in post(client).headers


# --- CORS ---------------------------------------------------------------------------------------

def test_the_preflight_from_the_portfolio_site_is_allowed(make_client):
    client, _ = make_client()
    response = client.options(
        "/chat",
        headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert "POST" in response.headers["access-control-allow-methods"]


def test_a_preflight_from_another_site_is_refused(make_client):
    client, _ = make_client()
    response = client.options(
        "/chat", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"}
    )
    assert response.status_code == 400 and "access-control-allow-origin" not in response.headers


def test_responses_carry_the_allow_origin_header_only_for_the_allowed_site(make_client):
    client, _ = make_client()
    allowed = client.post("/chat", json={"chat_id": CHAT_ID, "question": "hi"}, headers={"Origin": ORIGIN})
    other = client.post("/chat", json={"chat_id": CHAT_ID, "question": "hi"}, headers={"Origin": "https://evil.example"})
    assert allowed.headers["access-control-allow-origin"] == ORIGIN
    assert "access-control-allow-origin" not in other.headers
    # CORS is enforced by browsers, not by the server: a non-browser caller is still served, which is
    # exactly why the rate limit and input limits exist.
    assert other.status_code == 200


def test_the_default_origins_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://a.example, https://b.example")
    client = TestClient(api.create_app())
    response = client.options(
        "/chat", headers={"Origin": "https://b.example", "Access-Control-Request-Method": "POST"}
    )
    assert response.headers["access-control-allow-origin"] == "https://b.example"


def test_health_check(make_client):
    client, _ = make_client()
    assert client.get("/health").json() == {"status": "ok"}
