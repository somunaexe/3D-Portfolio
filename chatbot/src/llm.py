"""The swappable LLM: Ollama for development, OpenAI for demos.

Only the LLM is swappable. The embedding model is fixed (see indexing.embedding_function),
because stored and query vectors must come from the same model.

    LLM_PROVIDER=ollama  (default)   OLLAMA_MODEL=llama3.1:8b   OLLAMA_BASE_URL=http://localhost:11434
        Ollama CLOUD (no local model, no download): OLLAMA_BASE_URL=https://ollama.com, OLLAMA_API_KEY=...,
        and OLLAMA_MODEL=<a name from `curl https://ollama.com/api/tags`>. With a key set, it is sent as
        "Authorization: Bearer <key>". A local server needs no key.
    LLM_PROVIDER=openai              OPENAI_MODEL=gpt-4o-mini    OPENAI_API_KEY=...   (read by LangChain)
    LLM_TIMEOUT_SECONDS              give up on a stuck model. Default 300 for Ollama on this computer (a CPU can take
                                     minutes per answer), 30 for hosted models (a public endpoint must not hang)

Providers are imported lazily so you only need the one you use installed and configured.
"""
import os
from urllib.parse import urlparse


def request_timeout():
    """Seconds to wait for the model. A local model on a CPU can legitimately take over a minute per answer;
    hosted models answer in seconds, and a public endpoint must not hang on a stuck one."""
    override = os.environ.get("LLM_TIMEOUT_SECONDS")
    if override:
        return float(override)
    provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
    host = urlparse(os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).hostname or ""
    return 300.0 if provider == "ollama" and host in ("localhost", "127.0.0.1", "::1") else 30.0


def describe_llm():
    """One line saying which model is configured, for messages. Never includes a key."""
    provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
    if provider == "openai":
        return f"openai, model {os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')}"
    model = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
    url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    return f"{provider}, model {model} at {url}"


def troubleshooting_hint(error=None):
    description = f"{type(error).__name__} {error}".lower() if error is not None else ""
    if "timeout" in description or "timed out" in description:
        return ("The model took too long to answer (a local model on a CPU can be slow). Raise LLM_TIMEOUT_SECONDS "
                "(for example 600), or use a smaller or hosted model.")
    if os.environ.get("LLM_PROVIDER", "ollama").lower() == "openai":
        return "Check that OPENAI_API_KEY is set and valid, and that you have network access."
    return ("Is Ollama running, and is the model downloaded? Try `ollama list` (and `ollama pull <model>`). "
            "Run `python chatbot/src/check_setup.py` to test each piece.")


def get_llm():
    provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
    timeout = request_timeout()
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        client_kwargs = {"timeout": timeout}
        api_key = os.environ.get("OLLAMA_API_KEY")
        if api_key:   # Ollama cloud authenticates with a bearer token
            client_kwargs["headers"] = {"Authorization": f"Bearer {api_key}"}
        return ChatOllama(
            model=os.environ.get("OLLAMA_MODEL", "llama3.1:8b"),
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
            client_kwargs=client_kwargs,
        )
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), temperature=0, timeout=timeout, max_retries=1)
    raise ValueError(f"Unknown LLM_PROVIDER {provider!r}: use 'ollama' or 'openai'")
