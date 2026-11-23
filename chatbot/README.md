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

## Trying it without Redis

`python chatbot/src/chat.py --repl` opens an interactive chat that remembers the conversation inside that one window, so you
can test follow-up questions ("What technologies did you use there?") without installing Redis. It uses Redis automatically
if it is running. The real service always uses Redis.

## If something doesn't work

Run `python chatbot/src/check_setup.py` from the repo root. It checks each piece in order (libraries, CV chunks, vector
database, retrieval, Redis, the language model) and prints what to fix. `chat.py` also prints which model it is using, and
a plain error (not a stack trace) if the model can't be reached or returns nothing.

## Settings (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OLLAMA_MODEL` / `OLLAMA_BASE_URL` | `llama3.1:8b` / `http://localhost:11434` | |
| `OLLAMA_API_KEY` | - | only for Ollama cloud; sent as a bearer token |
| `OPENAI_MODEL` / `OPENAI_API_KEY` | `gpt-4o-mini` / - | |
| `LLM_TIMEOUT_SECONDS` | `300` for Ollama on this computer, else `30` | give up on a stuck model (a local model on a CPU can take minutes per answer; a follow-up makes two calls) |
| `REDIS_URL` | `redis://localhost:6379/0` | |
| `ALLOWED_ORIGINS` | `https://somunaexe.github.io,http://localhost:5173` | sites allowed to call it from a browser |
| `RATE_LIMIT_PER_MINUTE` | `20` | per client IP |
| `MAX_QUESTION_CHARS` | `200` | |
| `TRUST_X_REAL_IP` | off | set `true` behind Railway so the rate limit uses each visitor's real IP (see below) |
| `RETRIEVAL_CONCURRENCY` | `2` | how many embedding lookups may run at once (bounds memory) |

## Things to know

- **CV source:** `data/Main_CV_Improved.docx` is the tagged, phone-number-redacted copy. To rebuild it from the
  full CV: `python src/tag_cv_headings.py FULL.docx tagged.docx && python src/redact_cv.py tagged.docx data/Main_CV_Improved.docx`.
  Re-run `indexing.py --index` after any change.
- **Behind a proxy or host:** start uvicorn with `--proxy-headers --forwarded-allow-ips=<proxy IP>`, otherwise every
  visitor looks like the proxy's address and shares one rate-limit bucket.
- **CORS only constrains browsers.** curl and scripts are not blocked by it; the rate limit and input limits are
  what protect the LLM bill. If you use OpenAI, also set a monthly spend cap in your OpenAI account.
- **Conversations** live in Redis for 24 hours after the last message (last 10 turns).

## Deploying to Railway

Steps follow Railway's docs (Dockerfiles, Monorepo, Healthchecks, Redis, Variables, Public networking). The image
builds the vector index at build time, so a container starts ready and offline-capable; changing the CV means redeploying.

1. **Plan.** The Hobby plan ($5/month, which counts toward usage) is the sensible choice. The Free plan limits a service to
   0.5 GB RAM and can sleep when idle, so a recruiter's first question could wait for a cold start. This service uses
   roughly 0.3 GB.
2. **Create the project:** *New Project -> Deploy from GitHub repo -> 3D-Portfolio*. Deploy from `main` once this is merged
   (or pick the feature branch to test first).
3. **Service Settings -> Root Directory:** `/chatbot`. Railway then finds `chatbot/Dockerfile` by itself.
4. **Add Redis:** *+ New -> Database -> Redis* in the same project.
5. **Service Variables** (on the chatbot service, not Redis):

   | Variable | Value |
   |---|---|
   | `REDIS_URL` | `${{Redis.REDIS_URL}}` (the part before the dot is the Redis service's name) |
   | `LLM_PROVIDER` | `openai` |
   | `OPENAI_API_KEY` | your key (set a monthly spend cap on the OpenAI account first) |
   | `ALLOWED_ORIGINS` | `https://somunaexe.github.io` (comma-separate more origins if needed) |
   | `TRUST_X_REAL_IP` | `true` |

   Optional: `OPENAI_MODEL` (default `gpt-4o-mini`), `RATE_LIMIT_PER_MINUTE`, `LLM_TIMEOUT_SECONDS`.
6. **Settings -> Networking -> Generate Domain** to get a public `https://<name>.up.railway.app` address.
7. **Settings -> Healthcheck Path:** `/health`.
8. **Check it:** open `https://<your-domain>/health` (should show `{"status":"ok"}`), then try a question:
   `curl -s https://<your-domain>/chat -H 'Content-Type: application/json' -d '{"chat_id":"my-visitor-id-0123456789","question":"What did you do at Entain?"}'`
9. **Point the website at it:** in the GitHub repo, *Settings -> Secrets and variables -> Actions -> Variables*, add
   `VITE_CHATBOT_URL` = `https://<your-domain>`, then push to `main` so the site rebuilds with the chat icon.

Why `TRUST_X_REAL_IP=true`: Railway's proxy passes the visitor's real address in the `X-Real-IP` header; without it every
visitor appears to come from Railway's proxy and they would all share one rate-limit allowance. Do not turn it on for a server
that can be reached directly, because then anyone could send a fake `X-Real-IP` to dodge the limit.

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
