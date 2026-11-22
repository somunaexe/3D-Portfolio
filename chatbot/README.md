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
ollama pull llama3.1:8b               # or use Ollama cloud / OpenAI, see "Choosing an LLM" below
uvicorn api:app --app-dir src --port 8000
```

```bash
curl -s localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"chat_id":"my-visitor-id-0123456789","question":"What did you do at Entain?"}'
```

`chat_id` must be 16-64 characters (letters, digits, `_`, `-`). Have the website generate one per
visitor, e.g. `crypto.randomUUID()`. There is no login, so the id is what keeps conversations apart.

## Choosing an LLM

| Where the model runs | Settings | Disk | Needs |
|---|---|---|---|
| **Ollama cloud** (open models on Ollama's servers) | `LLM_PROVIDER=ollama` `OLLAMA_BASE_URL=https://ollama.com` `OLLAMA_API_KEY=...` `OLLAMA_MODEL=<name>` | none | an Ollama account + API key, and a paid plan or usage credits |
| Local Ollama | `LLM_PROVIDER=ollama` `OLLAMA_MODEL=llama3.1:8b` | ~5 GB | RAM; slow without a GPU |
| OpenAI | `LLM_PROVIDER=openai` `OPENAI_API_KEY=...` | none | an OpenAI key |

For Ollama cloud, create a key at https://ollama.com/settings/keys (no Ollama install needed), then list the model names
the direct API accepts: `curl https://ollama.com/api/tags` (these differ from the `:cloud` names the CLI uses).
Check your credits with `curl https://ollama.com/api/balance -H "Authorization: Bearer $OLLAMA_API_KEY"`.
Keep the key in your environment or a git-ignored `.env`, never in the code or the website.

## Settings (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OLLAMA_MODEL` / `OLLAMA_BASE_URL` | `llama3.1:8b` / `http://localhost:11434` | |
| `OLLAMA_API_KEY` | - | only for Ollama cloud; sent as a bearer token |
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

## The chat widget on the website

`src/components/ChatWidget.jsx` is a chat icon fixed to the bottom-right of the portfolio. Hovering shows "Ask me about
Somuna."; clicking opens a small panel that doesn't block the page. It calls this service's `POST /chat`.

- **Development:** `npm run dev` points it at `http://localhost:8000` automatically; start the service first.
- **Production:** set `VITE_CHATBOT_URL` to the deployed service's URL when building. In GitHub that is the repo variable
  *Settings > Secrets and variables > Actions > Variables > `VITE_CHATBOT_URL`* (the deploy workflow passes it to the build).
  With no URL, the icon is not shown, so the site never ships a chatbot that can't answer.
- The service must allow the site's origin: set `ALLOWED_ORIGINS` (the default already includes
  `https://somunaexe.github.io` and `http://localhost:5173`).
- A visitor's `chat_id` (a random UUID) and the conversation are kept in `sessionStorage`, so a reload keeps the chat and
  closing the tab ends it.

## Tests

```bash
pytest          # needs no LLM; uses a real redis-server if installed, else fakeredis
python src/probe.py "Have you used Docker?"   # see which chunks retrieval returns
```
