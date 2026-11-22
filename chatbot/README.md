# Portfolio chatbot

A recruiter-facing chatbot over the CV. A separately deployable Python service (GitHub Pages
can't run it). The design is in the "Portfolio RAG Chatbot - Design" doc.

```
POST /chat  {"chat_id": "...", "question": "..."}  ->  {"answer": "...", "sources": ["..."], "error": null}
```

Every response, including every failure, has that same three-field shape.

## Run it

```bash
cd chatbot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

python src/indexing.py --index        # chunk the CV, embed it, store it in chroma_db/ (rebuilds from scratch)
redis-server &                        # conversation memory
ollama pull llama3.1:8b               # or set LLM_PROVIDER=openai and OPENAI_API_KEY
uvicorn api:app --app-dir src --port 8000
```

```bash
curl -s localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"chat_id":"my-visitor-id-0123456789","question":"What did you do at Entain?"}'
```

`chat_id` must be 16-64 characters (letters, digits, `_`, `-`). Have the website generate one per
visitor, e.g. `crypto.randomUUID()`. There is no login, so the id is what keeps conversations apart.

## Settings (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OLLAMA_MODEL` / `OLLAMA_BASE_URL` | `llama3.1:8b` / `http://localhost:11434` | |
| `OPENAI_MODEL` / `OPENAI_API_KEY` | `gpt-4o-mini` / - | |
| `LLM_TIMEOUT_SECONDS` | `30` | give up on a stuck model |
| `REDIS_URL` | `redis://localhost:6379/0` | |
| `ALLOWED_ORIGINS` | `https://somunaexe.github.io,http://localhost:5173` | sites allowed to call it from a browser |
| `RATE_LIMIT_PER_MINUTE` | `20` | per client IP |
| `MAX_QUESTION_CHARS` | `200` | |

## Things to know

- **CV source:** `data/Main_CV_Improved.docx` is the tagged, phone-number-redacted copy. To rebuild it from the
  full CV: `python src/tag_cv_headings.py FULL.docx tagged.docx && python src/redact_cv.py tagged.docx data/Main_CV_Improved.docx`.
  Re-run `indexing.py --index` after any change.
- **Behind a proxy or host:** start uvicorn with `--proxy-headers --forwarded-allow-ips=<proxy IP>`, otherwise every
  visitor looks like the proxy's address and shares one rate-limit bucket.
- **CORS only constrains browsers.** curl and scripts are not blocked by it; the rate limit and input limits are
  what protect the LLM bill. If you use OpenAI, also set a monthly spend cap in your OpenAI account.
- **Conversations** live in Redis for 24 hours after the last message (last 10 turns).

## Tests

```bash
pytest          # needs no LLM; uses a real redis-server if installed, else fakeredis
python src/probe.py "Have you used Docker?"   # see which chunks retrieval returns
```
