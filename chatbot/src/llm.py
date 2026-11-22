"""The swappable LLM: Ollama for development, OpenAI for demos.

Only the LLM is swappable. The embedding model is fixed (see indexing.embedding_function),
because stored and query vectors must come from the same model.

    LLM_PROVIDER=ollama  (default)   OLLAMA_MODEL=llama3.1:8b   OLLAMA_BASE_URL=http://localhost:11434
    LLM_PROVIDER=openai              OPENAI_MODEL=gpt-4o-mini    OPENAI_API_KEY=...   (read by LangChain)

Providers are imported lazily so you only need the one you use installed and configured.
"""
import os


def get_llm():
    provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.environ.get("OLLAMA_MODEL", "llama3.1:8b"),
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
        )
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    raise ValueError(f"Unknown LLM_PROVIDER {provider!r}: use 'ollama' or 'openai'")
