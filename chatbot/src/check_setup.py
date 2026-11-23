"""Check each piece of the chatbot in order and say what to fix.

    python chatbot/src/check_setup.py

Run it from the repo root. Redis is optional (without it the chatbot answers but has no memory).

Every step runs in its OWN process. Some libraries (the ONNX model runtime, the vector database) are native code; if one
crashes, Python cannot print an error and the whole program just stops, silently. In a separate process a crash is
reported with its exit code and where it happened, and the remaining steps still run.
"""
import os
import platform
import subprocess
import sys
import time
from importlib import import_module

ME = os.path.abspath(__file__)
STEPS = []   # filled by @step, in order

CRASH_ON_IMPORT_ADVICE = (
    "A crash while loading usually means a clashing Microsoft C++ runtime DLL (common with Anaconda's Python) or an "
    "incompatible build. Create the virtual environment from a python.org Python instead of Anaconda's."
)


def conda_warning(prefix):
    """Warning text if the Python in use comes from Anaconda/Miniconda, else None."""
    if any(marker in prefix.lower() for marker in ("anaconda", "miniconda", "conda")):
        return ("This Python comes from Anaconda/conda. It bundles its own, older Microsoft C++ runtime, which is a known "
                "cause of silent crashes in onnxruntime on Windows.")
    return None


def step(name, hint, required=True, timeout=120):
    def decorate(function):
        STEPS.append({"name": name, "hint": hint, "required": required, "timeout": timeout, "run": function})
        return function
    return decorate


# --- the steps (each runs in a child process) ------------------------------------------------------

def _loads(module):
    def load():
        loaded = import_module(module)
        return f"version {getattr(loaded, '__version__', '?')}"
    return load


for _module, _why in [
    ("numpy", "numpy is the base of the numeric libraries"),
    ("onnxruntime", "onnxruntime runs the embedding model; a crash here usually means the build doesn't suit your CPU"),
    ("chromadb", "chromadb is the vector database"),
]:
    step(f"{_module} loads", _why + ". " + CRASH_ON_IMPORT_ADVICE)(_loads(_module))


@step("other libraries installed", "Activate the virtual environment, then: pip install -r chatbot/requirements-dev.txt")
def _():
    missing = []
    for library in ["docx", "langchain_core", "langchain_ollama", "langchain_openai", "redis", "fastapi", "uvicorn"]:
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


@step("retrieval finds the right chunk", "Re-run indexing: python chatbot/src/indexing.py --index", timeout=180)
def _():
    from retrieval import retrieve
    return "top result for 'What did you do at Entain?' is " + repr(retrieve("What did you do at Entain?", k=1)[0]["title"])


@step("Redis (optional, for memory)", "Not needed for a first test. Without Redis the chatbot answers but forgets earlier messages.", required=False, timeout=15)
def _():
    from memory import ChatMemory
    ChatMemory().client.ping()
    return "reachable"


@step("the language model answers", "For Ollama: is it running, and does `ollama list` show the model? (chat.py prints the same hint)", timeout=240)
def _():
    from llm import describe_llm, get_llm, troubleshooting_hint
    print(f"using {describe_llm()}")
    started = time.time()
    try:
        reply = get_llm().invoke("Reply with the single word: ready").content
    except Exception as error:
        raise RuntimeError(f"{error}. {troubleshooting_hint()}") from error
    if not str(reply).strip():
        raise ValueError("the model returned an EMPTY reply")
    return f"replied {str(reply).strip()[:40]!r} in {time.time() - started:.1f}s"


# --- running a step in its own process --------------------------------------------------------------

CRASH_CODES = {
    0xC0000005: "access violation (a native library touched memory it shouldn't have)",
    0xC000001D: "illegal instruction (a library was built for CPU features yours may lack)",
    0xC0000409: "fast-fail / stack buffer overrun inside a native library",
    0xC0000135: "a required DLL was not found",
    0xC000007B: "a DLL is the wrong kind for this Python (32-bit vs 64-bit)",
    0xC0000142: "a DLL failed to initialise",
}


def describe_exit(code):
    """Words for a process exit code that is neither success (0) nor a normal failure (1)."""
    unsigned = code & 0xFFFFFFFF
    if unsigned in CRASH_CODES:
        return f"crashed: exit code {hex(unsigned)}, {CRASH_CODES[unsigned]}"
    if code < 0:   # POSIX: killed by a signal
        return f"crashed: killed by signal {-code}"
    return f"crashed: exit code {code}"


def run_isolated(argv, timeout):
    """Run a command; returns (status, text) with status 'ok', 'fail', 'crash' or 'timeout'."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        done = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return "timeout", f"no answer after {timeout} seconds"
    text = done.stdout.strip()
    if done.returncode == 0:
        return "ok", text
    if done.returncode == 1:
        return "fail", text or done.stderr.strip()
    crash_trace = "\n".join(done.stderr.strip().splitlines()[-8:])   # faulthandler's "where it died"
    return "crash", describe_exit(done.returncode) + (("\n" + crash_trace) if crash_trace else "")


def run_child(index):
    """Entry point of the child process: run one step; exit 0 = ok, 1 = a normal Python error."""
    sys.path.insert(0, os.path.dirname(ME))
    try:
        detail = STEPS[index]["run"]()
    except Exception as error:   # a normal failure: say what it was
        print(f"{type(error).__name__}: {error}")
        return 1
    print(detail or "")
    return 0


def main():
    print(f"Python {sys.version.split()[0]} on {platform.system()} {platform.machine()} ({platform.processor() or 'CPU unknown'})")
    print(f"Python installed at: {sys.base_prefix}")
    warning = conda_warning(sys.base_prefix)
    if warning:
        print(f"WARNING: {warning}")
    print()
    failures = []
    for index, spec in enumerate(STEPS):
        status, text = run_isolated([sys.executable, "-X", "faulthandler", ME, "--run", str(index)], spec["timeout"])
        lines = text.splitlines() or [""]
        ok = status == "ok"
        label = "OK  " if ok else ("FAIL" if spec["required"] else "skip")
        first = lines[0] if ok else (f"{lines[0]}" if status != "fail" else lines[0])
        print(f"[{label}] {spec['name']}" + (f": {first}" if first else ""))
        for extra in lines[1:]:
            print(f"         {extra}")
        if not ok:
            print(f"         -> {spec['hint']}")
            if spec["required"]:
                failures.append(spec["name"])
    print()
    if failures:
        print("Needs attention: " + ", ".join(failures))
        return 1
    print('Everything needed is working. Try: python chatbot/src/chat.py my-test-chat-0123456789 "What did you do at Entain?"')
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--run":
        sys.exit(run_child(int(sys.argv[2])))
    sys.exit(main())
