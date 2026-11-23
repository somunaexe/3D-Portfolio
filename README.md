# Personal Portfolio Website

An interactive 3D portfolio for **Somuna Nzenwa** (Artificial Intelligence MSc graduate; DevOps, AI/ML and full-stack engineering), with an AI assistant, **Ezem**, that answers questions about my CV.

**Live site:** https://somunaexe.github.io

---

## What's in it

- **3D hero and sections** built with React and Three.js: about, work experience, projects, reviews and contact.
- **Projects explorer** (`/projects.html`): a standalone page to filter by platform, stack and language, sort by name or date, and page through every project.
- **Six colour themes** (Light, Bulfighter Light, Bulwriter Light, Bulwriter Dark, Bulfighter Dark, Dark) from a slider in the navbar. Colours are checked for WCAG contrast, and the choice is remembered.
- **Ezem, a chatbot** in the bottom-right corner. It answers recruiters' questions from my CV, cites its sources and says so when the CV doesn't contain the answer. The service lives in [`chatbot/`](chatbot/README.md).

## How it is put together

```
visitor's browser ──► static site (GitHub Pages and S3)
                         │  POST /chat
                         ▼
                  Ezem service (FastAPI on Railway)
                   ├─ ChromaDB   the CV, split into 38 searchable chunks
                   ├─ Redis      conversation memory, rate limiting, 30-day question log
                   └─ OpenAI     writes the answer (a local Ollama model works in development)
```

Ezem retrieves the CV chunks closest to the question, adds any role or project named in it, and asks the model to answer using only those excerpts. A feedback loop (an opt-in question log, a report of unanswered questions and a golden question set) helps improve it without letting visitors steer the answers. See [`chatbot/README.md`](chatbot/README.md) for the details, the settings and the tests.

## Built with

React, Vite, JavaScript, Node.js, Three.js, Tailwind CSS, Python, FastAPI, LangChain, ChromaDB, Redis, OpenAI, Docker, Railway, AWS (S3), GitHub Actions and Git.

## Run it locally

```bash
npm install
npm run dev          # the site at http://localhost:5173
npm run build        # a production build in dist/
npm run lint
```

The chat icon only appears when the site knows where the chatbot is. In development it assumes `http://localhost:8000`; for a production build set `VITE_CHATBOT_URL` (see `.env.example`). To run the chatbot itself, follow [`chatbot/README.md`](chatbot/README.md).

## Deployment

Every push to `main` runs [`.github/workflows/sync.yml`](.github/workflows/sync.yml), which builds the site, syncs it to an S3 bucket and publishes it to the `main` branch of `somunaexe/somunaexe.github.io` (served by GitHub Pages). The chatbot's address comes from the repository variable `VITE_CHATBOT_URL`, and is baked in at build time. The chatbot service redeploys on Railway when `main` changes.

## Project structure

```
.
├── index.html, projects.html   # the two pages (multi-page Vite build)
├── src/
│   ├── sections/               # Hero, About, Experience, Projects, Reviews, Contact, Footer
│   ├── pages/                  # the projects explorer
│   ├── components/             # theme slider, chat widget, 3D models
│   ├── constants/              # work experience, projects, themes
│   ├── hooks/, lib/            # theme store, project search, chat client
│   └── index.css               # theme colours and animations
├── public/                     # images, icons and 3D assets
├── scripts/                    # tooling, e.g. the animated logo generator
├── chatbot/                    # Ezem: FastAPI service, CV data, tests, evaluation questions
└── .github/workflows/          # build and deploy
```
