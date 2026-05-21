# LeoChat 🚀

> **LEO** – a friendly, state‑of‑the‑art AI chat assistant built with **FastAPI**, **SQLite**, and the **Groq LLM**. It provides a clean, glass‑morphism UI that focuses solely on the chat area, making the conversation experience sleek and distraction‑free.
# LeoChat — Stateful Chatbot Engine

A small, production-oriented stateful chatbot built with FastAPI, a Groq-backed LLM client, and SQLite session storage. The project uses a decoupled three-tier architecture (API, orchestration, persistence) and includes a simple RAG (retrieval-augmented generation) pipeline.

**Repository layout (important files):**
- `main.py` — FastAPI application and static mounting.
- `api/chat.py` — HTTP API endpoints: `/api/chat`, `/api/knowledge`, `/api/session/clear`.
- `core/llm.py` — Lightweight Groq LLM client wrapper (async HTTPX).
- `core/memory.py` — Sliding-window conversation memory manager.
- `core/prompt.py` — Message assembly and default system prompt.
- `core/rag.py` — Simple chunking + TF-IDF retrieval engine (no external vectors).
- `db/session_store.py` — SQLite-backed message & knowledge store.
- `.env` — Local environment variables (must NOT be committed).

## Features
- Stateful conversations saved per `session_id` in `sessions.db`.
- Custom, session-scoped knowledge documents via `/api/knowledge` (RAG-enabled retrieval).
- Sliding-window memory to bound context size (`MAX_HISTORY_TURNS`).
- Async LLM calls to Groq using `httpx.AsyncClient`.
  
## Live Demo

🚀 Experience the high-performance search engine live: **https://leochat-1.onrender.com**

## Quick start (Windows)

1. Create and activate a virtual env, then install deps:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Create a `.env` file in the project root with the values below, then start the app:

```bash
# Example .env
GROQ_API_KEY=your_real_groq_api_key_here
# Optional overrides
GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
LLM_MODEL=llama-3.1-8b-instant
DB_PATH=sessions.db
MAX_HISTORY_TURNS=5
LOG_LEVEL=INFO
```

```bash
# Run locally (development)
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open the web UI at `http://127.0.0.1:8000/` (serves `static/index.html`).

## Environment variables
- `GROQ_API_KEY` (required): Bearer key for Groq API. Keep this secret — do not commit.
- `GROQ_API_URL`: API endpoint (defaults to Groq chat completions URL).
- `LLM_MODEL`: Model name to request from Groq.
- `DB_PATH`: Path to SQLite DB file (default `sessions.db`).
- `MAX_HISTORY_TURNS`: Number of conversation turns to keep for context.
- `LOG_LEVEL`: `INFO`, `DEBUG`, etc.

## HTTP API

1) POST `/api/chat` — chat with the assistant

Request JSON:

```json
{
   "message": "Hello, how are you?",
   "session_id": "<optional session id>",
   "system_prompt": "<optional system instructions>"
}
```

Response:

```json
{
   "response": "...assistant text...",
   "session_id": "...",
   "usage": { "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0 }
}
```

2) POST `/api/knowledge` — save session-scoped documents for RAG

Request JSON:
```json
{ "session_id": "<id>", "content": "Long document text to index for this session" }
```

3) POST `/api/session/clear` — clears conversation and knowledge for a session

Request body: form param `session_id` (string)

## Design notes
- RAG: `core/rag.py` chunks documents and uses an internal TF-IDF engine to retrieve relevant chunks at query time — no external embeddings needed.
- Memory: `core/memory.py` applies a sliding window (controlled by `MAX_HISTORY_TURNS`) and persists messages in `db/session_store.py`.
- LLM: `core/llm.py` performs async requests to Groq and returns token usage metadata for cost monitoring.

## Security & best practices
- Never commit `.env` or secrets. Add them to `.gitignore` (already present).
- If a secret is accidentally committed, rotate/revoke it immediately and remove it from history (we did this for the repo).
- Prefer using a secrets manager for production deployments (e.g., GitHub Secrets, Azure Key Vault, AWS Secrets Manager).

## Tests & local checks
- No formal test suite included. You can smoke-test endpoints with `curl` or tools like Postman.

Example `curl` usage:

```bash
curl -s -X POST http://127.0.0.1:8000/api/chat \
   -H "Content-Type: application/json" \
   -d '{"message": "Say hi", "session_id": "test-session"}'
```

## Contributing
- Open an issue or PR. Keep changes focused and add tests where appropriate.

## License
- Add a license file if you plan to open-source this project.

---
If you'd like, I can:
- run a quick scan for other secrets,
- add a short CONTRIBUTING.md or LICENSE,
- or create a small Postman collection for the API.

File: [README.md](README.md)

4. **Run the server**:
   ```bash
   uvicorn main:app --reload
   ```
   The API will be available at `http://127.0.0.1:8000` and the UI at `http://127.0.0.1:8000/static/`.

---

## ▶️ Usage

- Open the UI in a browser (default: `http://127.0.0.1:8000/static/`).
- Type a message in the input bar and hit **Enter** or click **Send**.
- LEO replies using the configured Groq model.
- Your conversation is automatically persisted in `sessions.db`.

### API Endpoints (FastAPI)
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Send a user message and receive LEO's response. |
| `GET`  | `/history/{session_id}` | Retrieve chat history for a session. |
| `POST` | `/session/new` | Create a new chat session. |

---

## 🔐 Security Note

The repository is protected by GitHub’s **Push‑Protection** to prevent accidental exposure of secrets. **Never** commit `.env` or any API keys. The file is listed in `.gitignore` automatically.

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Open an issue for bugs or feature ideas.
- Submit a pull request with clear description of changes.
- Keep the UI/UX consistent with the glass‑morphism theme.

Please make sure your changes pass the existing tests (if any) and follow PEP 8 style guidelines.

---

### 🎉 Happy chatting with LEO!
