"""The analytics log: what it keeps, what it must never keep, and that it can never break a chat."""
import json
import sys
from pathlib import Path

import pytest
import redis
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import analytics  # noqa: E402
import api  # noqa: E402
import indexing  # noqa: E402
import report  # noqa: E402
from fakes import DeadRedis, FakeLLM  # noqa: E402
from memory import ChatMemory  # noqa: E402
from ratelimit import RateLimiter  # noqa: E402

CHAT_ID = "analytics-chat-0123456789"


@pytest.fixture(scope="module")
def db_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("chroma")
    indexing.index_chunks(indexing.build_chunks(), db_dir=path)
    return path


@pytest.fixture
def app_client(db_dir, redis_client):
    def build(llm=None, log="real"):
        fake = llm or FakeLLM()
        app = api.create_app(allowed_origins=["http://localhost:5173"], trust_x_real_ip=False)
        app.dependency_overrides[api.get_memory] = lambda: ChatMemory(redis_client)
        app.dependency_overrides[api.get_chat_llm] = lambda: fake.runnable
        app.dependency_overrides[api.get_limiter] = lambda: RateLimiter(redis_client, limit=1000)
        app.dependency_overrides[api.get_chat_options] = lambda: {"db_dir": db_dir}
        question_log = analytics.QuestionLog(redis_client) if log == "real" else log
        app.dependency_overrides[api.get_question_log] = lambda: question_log
        return TestClient(app), question_log

    return build


def ask(client, question="What did you do at Entain?"):
    return client.post("/chat", json={"chat_id": CHAT_ID, "question": question})


# --- privacy ------------------------------------------------------------------------------------

def test_emails_and_phone_numbers_in_a_question_are_masked_before_storing():
    text = analytics.mask_personal_details("Email me at jane.doe@example.com or call +44 7700 900123 about the role")
    assert "jane.doe" not in text and "7700" not in text
    assert "[email]" in text and "[number]" in text and "about the role" in text


def test_ordinary_numbers_survive_masking():
    assert analytics.mask_personal_details("Did you get 95% accuracy in 2025 with 50 users?") == "Did you get 95% accuracy in 2025 with 50 users?"


def test_a_logged_event_holds_no_answer_chat_id_or_ip(app_client, redis_client):
    client, _ = app_client()
    ask(client)
    (raw,) = redis_client.zrange(analytics.KEY, 0, -1)
    event = json.loads(raw)
    assert set(event) == {"id", "ts", "status", "question", "latency_ms", "standalone", "had_history",
                          "retrieved", "cited", "cited_titles", "supported"}
    assert CHAT_ID not in raw and "testclient" not in raw and "They built it" not in raw


# --- recording ----------------------------------------------------------------------------------

def test_a_question_is_recorded_with_what_was_retrieved_and_cited(app_client, redis_client):
    client, question_log = app_client()
    ask(client)
    (event,) = question_log.events()
    assert event["status"] == "ok" and event["question"] == "What did you do at Entain?"
    assert len(event["retrieved"]) == 10
    assert event["supported"] is True and len(event["cited"]) == 1   # the fake model cites [1]


def test_an_answer_with_no_citation_is_marked_unsupported(app_client):
    client, question_log = app_client(llm=FakeLLM(answer="I don't have that information."))
    ask(client, "What is your favourite food?")
    (event,) = question_log.events()
    assert event["supported"] is False and event["cited"] == []


def test_a_pipeline_failure_is_recorded_as_an_error_without_details(app_client):
    client, question_log = app_client(llm=FakeLLM(error=RuntimeError("secret provider detail")))
    assert ask(client).status_code == 503
    (event,) = question_log.events()
    assert event["status"] == "error" and "secret" not in json.dumps(event)


def test_nothing_is_logged_when_analytics_is_off(app_client, redis_client):
    client, _ = app_client(log=None)
    assert ask(client).status_code == 200
    assert redis_client.zcard(analytics.KEY) == 0


def test_analytics_is_off_unless_explicitly_enabled(monkeypatch):
    monkeypatch.delenv("ANALYTICS_ENABLED", raising=False)
    assert analytics.enabled() is False
    for value in ("true", "TRUE", "1", "yes"):
        monkeypatch.setenv("ANALYTICS_ENABLED", value)
        assert analytics.enabled() is True
    monkeypatch.setenv("ANALYTICS_ENABLED", "false")
    assert analytics.enabled() is False


def test_a_broken_log_never_costs_the_visitor_their_answer(app_client):
    client, _ = app_client(log=analytics.QuestionLog(DeadRedis()))
    response = ask(client)
    assert response.status_code == 200 and response.json()["answer"]


# --- retention ----------------------------------------------------------------------------------

def event_at(ts, question="q"):
    return {"id": f"id{ts}", "ts": ts, "status": "ok", "question": question, "latency_ms": 5}


def test_entries_older_than_the_retention_window_are_deleted_on_the_next_write(redis_client):
    log = analytics.QuestionLog(redis_client, retention_days=30)
    day = 86400
    log.record(event_at(1_000_000_000, "ancient"))
    log.record(event_at(1_000_000_000 + 29 * day, "recent"))
    log.record(event_at(1_000_000_000 + 31 * day, "newest"))
    assert [e["question"] for e in log.events(now=1_000_000_000 + 31 * day)] == ["newest", "recent"]


def test_the_log_never_grows_past_its_ceiling(redis_client):
    log = analytics.QuestionLog(redis_client, max_entries=5)
    for number in range(12):
        log.record(event_at(2_000_000_000 + number, f"q{number}"))
    assert [e["question"] for e in log.events()] == [f"q{n}" for n in range(11, 6, -1)]


def test_the_whole_log_expires_if_traffic_stops(redis_client):
    analytics.QuestionLog(redis_client, retention_days=30).record(event_at(2_000_000_000))
    assert 0 < redis_client.ttl(analytics.KEY) <= 30 * 86400


def test_corrupt_entries_are_skipped_not_fatal(redis_client):
    redis_client.zadd(analytics.KEY, {"not json": 1})
    log = analytics.QuestionLog(redis_client)
    log.record(event_at(2_000_000_000, "fine"))
    assert [e["question"] for e in log.events()] == ["fine"]


# --- the report ---------------------------------------------------------------------------------

def make_event(question, supported=True, status="ok", latency=100, cited=("Entain",)):
    return {"status": status, "standalone": question, "supported": supported, "latency_ms": latency,
            "cited_titles": list(cited) if supported else [], "retrieved": [], "cited": [], "question": question, "ts": 1}


def test_the_report_groups_repeated_unsupported_questions_ignoring_case_and_punctuation():
    events = [make_event("What is your favourite food?", supported=False),
              make_event("what is your favourite food", supported=False),
              make_event("What did you do at Entain?")]
    summary = report.summarise(events)
    assert summary["unsupported"] == [("What is your favourite food?", 2)]
    assert summary["most_cited"] == [("Entain", 1)]


def test_the_report_counts_errors_and_latency_percentiles():
    events = [make_event("a", latency=ms) for ms in (100, 200, 300, 400)] + [make_event("b", status="error", latency=900)]
    summary = report.summarise(events)
    assert summary["total"] == 5 and summary["errors"] == 1
    assert summary["latency_ms_median"] == 300 and summary["latency_ms_p95"] == 900


def test_the_report_copes_with_an_empty_log(capsys):
    report.print_report(report.summarise([]), 7)
    assert "Nothing logged" in capsys.readouterr().out


def test_the_report_cli_prints_a_report_for_a_scheduled_run(monkeypatch, redis_client, capsys):
    """What Railway's weekly cron job runs: `python src/report.py --days 7`."""
    analytics.QuestionLog(redis_client).record(event_at(int(__import__("time").time()), "Do you know Rust?") | {"standalone": "Do you know Rust?", "supported": False, "cited_titles": [], "retrieved": [], "cited": []})
    monkeypatch.setattr(report.redis.Redis, "from_url", lambda *a, **k: redis_client)
    monkeypatch.setattr(sys, "argv", ["report.py", "--days", "7"])
    report.main()
    output = capsys.readouterr().out
    assert "Last 7 days: 1 question(s)" in output and "Do you know Rust?" in output


def test_the_report_cli_fails_loudly_when_redis_is_unreachable(monkeypatch):
    """A cron run that can't read Redis must exit non-zero, so Railway shows the run as failed."""
    monkeypatch.setattr(report.redis.Redis, "from_url", lambda *a, **k: DeadRedis())
    monkeypatch.setattr(sys, "argv", ["report.py"])
    with pytest.raises(SystemExit) as exit_info:
        report.main()
    assert "Could not read Redis" in str(exit_info.value)
