"""The swappable LLM: Ollama for development, OpenAI for demos.

Only the LLM is swappable. The embedding model is fixed (see indexing.embedding_function),
because stored and query vectors must come from the same model.

    LLM_PROVIDER=ollama  (default)   OLLAMA_MODEL=llama3.1:8b   OLLAMA_BASE_URL=http://localhost:11434
        Ollama CLOUD (no local model, no download): OLLAMA_BASE_URL=https://ollama.com, OLLAMA_API_KEY=...,
        and OLLAMA_MODEL=<a name from `curl https://ollama.com/api/tags`>. With a key set, it is sent as
        "Authorization: Bearer <key>". A local server needs no key.
    LLM_PROVIDER=openai              OPENAI_MODEL=gpt-4o-mini    OPENAI_API_KEY=...   (read by LangChain)
    LLM_TIMEOUT_SECONDS=30           give up on a stuck model (a public endpoint must not hang)

Providers are imported lazily so you only need the one you use installed and configured.
"""
import os


def describe_llm():
    """One line saying which model is configured, for messages. Never includes a key."""
    provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
    if provider == "openai":
        return f"openai, model {os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')}"
    model = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
    url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    return f"{provider}, model {model} at {url}"


def troubleshooting_hint():
    if os.environ.get("LLM_PROVIDER", "ollama").lower() == "openai":
        return "Check that OPENAI_API_KEY is set and valid, and that you have network access."
    return ("Is Ollama running, and is the model downloaded? Try `ollama list` (and `ollama pull <model>`). "
            "Run `python chatbot/src/check_setup.py` to test each piece.")


def get_llm():
    provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
    timeout = float(os.environ.get("LLM_TIMEOUT_SECONDS", "30"))
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
