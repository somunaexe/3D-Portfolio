"""Milestone 4: the HTTP door. FastAPI validates the request, calls chat.chat(), shapes the reply.

    uvicorn api:app --app-dir chatbot/src --port 8000

    POST /chat   {"chat_id": "...", "question": "..."}   ->   {"answer", "sources", "error"}

Everything it returns, including every failure, has that same three-field shape, so a client
never has to guess whether a call worked (that is the point of the `error` field in the design
doc). There is no RAG logic here: no embedding, retrieval or prompt building.

Settings (environment): ALLOWED_ORIGINS (comma-separated; the sites allowed to call this from a
browser), RATE_LIMIT_PER_MINUTE (default 20 per IP), MAX_QUESTION_CHARS (default 200), TRUST_X_REAL_IP
(set to true behind Railway, see client_ip), plus the LLM / Redis settings in llm.py and memory.py.
"""
import ipaddress
import logging
import os
import time
from functools import lru_cache

import redis
from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

import analytics
import chat as chat_pipeline
from llm import get_llm
from memory import REDIS_URL, ChatMemory
from ratelimit import RateLimiter

logger = logging.getLogger(__name__)

MAX_QUESTION_CHARS = int(os.environ.get("MAX_QUESTION_CHARS", "200"))
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "20"))
DEFAULT_ORIGINS = "https://somunaexe.github.io,http://localhost:5173"
TRUST_X_REAL_IP = os.environ.get("TRUST_X_REAL_IP", "").lower() in ("1", "true", "yes")


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # The client should generate an unguessable id (e.g. crypto.randomUUID()). There is no login, so
    # the id is the only thing separating one visitor's conversation from another's: hence min 16.
    chat_id: str = Field(pattern=r"^[A-Za-z0-9_-]{16,64}$")
    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)


class ChatResponse(BaseModel):
    answer: str | None = None
    sources: list[str] = []
    error: str | None = None


def failure(status, message, headers=None):
    return JSONResponse(status_code=status, content=ChatResponse(error=message).model_dump(), headers=headers)


def source_label(source):
    """{'section': 'Projects', 'title': 'Uber Clone'} -> 'Projects: Uber Clone' (the contract wants strings)."""
    section, title = source.get("section"), source["title"]
    return title if not section or section.lower() == title.lower() else f"{section}: {title}"


def source_labels(sources):
    labels = []
    for source in sources:
        label = source_label(source)
        if label not in labels:
            labels.append(label)
    return labels


def client_ip(request, trust_x_real_ip):
    """The visitor's address, for rate limiting.

    Behind Railway every connection arrives from Railway's proxy, so the socket address is the same for every
    visitor, and one shared bucket would let a single visitor use up everyone's allowance. Railway puts the real
    visitor in X-Real-IP. That header is only believed when asked for (TRUST_X_REAL_IP=true): on a server that
    can be reached directly, anyone could send a fake X-Real-IP and dodge the limit.
    """
    if trust_x_real_ip:
        try:
            return str(ipaddress.ip_address(request.headers.get("x-real-ip", "").strip()))
        except ValueError:
            pass   # missing or not an IP: fall back to the socket address
    return request.client.host if request.client else "unknown"


# --- dependencies (tests swap these out with app.dependency_overrides) --------------------------

@lru_cache
def get_redis():
    return redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=2, socket_connect_timeout=2)


def get_memory():
    return ChatMemory(get_redis())


@lru_cache
def get_chat_llm():
    return get_llm()


def get_limiter():
    return RateLimiter(get_redis(), limit=RATE_LIMIT_PER_MINUTE)


def get_chat_options():
    return {}


def get_question_log():
    """The analytics log, or None when ANALYTICS_ENABLED is not true (the default: nothing is kept)."""
    return analytics.QuestionLog(get_redis()) if analytics.enabled() else None


def create_app(allowed_origins=None, trust_x_real_ip=None):
    trust_x_real_ip = TRUST_X_REAL_IP if trust_x_real_ip is None else trust_x_real_ip
    origins = allowed_origins
    if origins is None:
        origins = [origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",") if origin.strip()]

    app = FastAPI(title="Portfolio chatbot", version="1.0")

    # CORS only tells BROWSERS which sites may read responses. It does not stop curl or a script, which is
    # why the rate limit and the input limits exist.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["POST"],
        allow_headers=["Content-Type"],
        expose_headers=["Retry-After", "X-Chat-Memory"],
        max_age=600,
    )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        first = exc.errors()[0]
        field = next((str(part) for part in reversed(first["loc"]) if part != "body"), "request")
        return failure(422, f"Invalid request: {field}: {first['msg']}")   # never echoes the visitor's input back

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        return failure(exc.status_code, str(exc.detail), headers=getattr(exc, "headers", None))

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception):
        logger.exception("unhandled error")
        return failure(500, "Something went wrong on our side. Please try again.")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # `def`, not `async def`: the pipeline blocks (embedding, Chroma, LLM calls), and FastAPI runs a plain
    # `def` endpoint in a worker thread. An `async def` here would freeze the whole server during each call.
    @app.post("/chat", response_model=ChatResponse)
    def post_chat(
        body: ChatRequest,
        request: Request,
        response: Response,
        memory: ChatMemory = Depends(get_memory),
        llm=Depends(get_chat_llm),
        limiter: RateLimiter = Depends(get_limiter),
        options: dict = Depends(get_chat_options),
        question_log=Depends(get_question_log),
    ):
        allowed, retry_after = limiter.check(client_ip(request, trust_x_real_ip))
        if not allowed:
            return failure(429, "Too many requests. Please wait a moment and try again.", {"Retry-After": str(retry_after)})

        started = time.perf_counter()
        try:
            result = chat_pipeline.chat(body.chat_id, body.question, memory=memory, llm=llm, **options)
        except Exception:
            logger.exception("chat pipeline failed")   # details stay in the server log, never in the response
            if question_log:
                question_log.record(analytics.build_event(body.question, status="error", latency_ms=(time.perf_counter() - started) * 1000))
            return failure(503, "The assistant is temporarily unavailable. Please try again shortly.")

        if question_log:   # after the answer exists; record() never raises, so it cannot cost the visitor a reply
            question_log.record(analytics.build_event(body.question, result, latency_ms=(time.perf_counter() - started) * 1000))

        if result.memory_error:
            logger.warning("memory degraded: %s", result.memory_error)
            response.headers["X-Chat-Memory"] = "unavailable"   # the answer is still good, just context-free
        return ChatResponse(answer=result.answer.answer, sources=source_labels(result.answer.sources))

    return app


app = create_app()
