"""Check each piece of the chatbot in order and say what to fix.

    python chatbot/src/check_setup.py

Run it from the repo root. Redis is optional (without it the chatbot answers but has no memory).
"""
import sys
import time
from importlib import import_module

REQUIRED_LIBRARIES = ["docx", "chromadb", "langchain_core", "langchain_ollama", "langchain_openai", "redis", "fastapi", "uvicorn"]
failures = []


def report(ok, name, detail="", hint="", required=True):
    status = "OK  " if ok else ("FAIL" if required else "skip")
    print(f"[{status}] {name}" + (f": {detail}" if detail else ""))
    if not ok:
        if hint:
            print(f"         -> {hint}")
        if required:
            failures.append(name)


def step(name, hint, required=True):
    """Run the decorated function; OK with its returned detail, or FAIL with the error."""
    def decorate(function):
        try:
            report(True, name, function() or "")
        except Exception as error:
            report(False, name, f"{type(error).__name__}: {error}", hint, required)
        return function
    return decorate


print(f"Python {sys.version.split()[0]}\n")


@step("libraries installed", "Activate the virtual environment, then: pip install -r chatbot/requirements-dev.txt")
def _():
    missing = []
    for library in REQUIRED_LIBRARIES:
        try:
            import_module(library)
        except ImportError:
            missing.append(library)
    if missing:
        raise ImportError("missing " + ", ".join(missing))


@step("CV chunks build", "Is chatbot/data/Main_CV_Improved.docx there? Did `git pull` finish?")
def _():
    from indexing import build_chunks
    return f"{len(build_chunks())} chunks"


@step("vector database has the CV", "Run: python chatbot/src/indexing.py --index   (the first run downloads an 80 MB model)")
def _():
    import chromadb
    from indexing import COLLECTION, DB_DIR, embedding_function
    collection = chromadb.PersistentClient(path=str(DB_DIR)).get_collection(COLLECTION, embedding_function=embedding_function())
    count = collection.count()
    if count == 0:
        raise ValueError("the collection is empty")
    return f"{count} chunks stored"


@step("retrieval finds the right chunk", "Re-run indexing: python chatbot/src/indexing.py --index")
def _():
    from retrieval import retrieve
    return "top result for 'What did you do at Entain?' is " + repr(retrieve("What did you do at Entain?", k=1)[0]["title"])


@step("Redis (optional, for memory)", "Not needed for a first test. Without Redis the chatbot answers but forgets earlier messages.", required=False)
def _():
    from memory import ChatMemory
    ChatMemory().client.ping()
    return "reachable"


@step("the language model answers", "See the hint printed by chat.py; for Ollama: is it running, and does `ollama list` show the model?")
def _():
    from llm import describe_llm, get_llm, troubleshooting_hint
    print(f"         using {describe_llm()}")
    started = time.time()
    try:
        reply = get_llm().invoke("Reply with the single word: ready").content
    except Exception as error:
        raise RuntimeError(f"{error}. {troubleshooting_hint()}") from error
    if not str(reply).strip():
        raise ValueError("the model returned an EMPTY reply (see the hint above)")
    return f"replied {str(reply).strip()[:40]!r} in {time.time() - started:.1f}s"


print()
if failures:
    print("Needs attention: " + ", ".join(failures))
    sys.exit(1)
print("Everything needed is working. Try: python chatbot/src/chat.py my-test-chat-0123456789 \"What did you do at Entain?\"")
