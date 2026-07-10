# 📖 DocuChat

Upload a PDF or text file, ask it questions, and get answers grounded in the exact passages they came from.

DocuChat is a full-stack Retrieval-Augmented Generation (RAG) app: a FastAPI backend handles auth, document ingestion, and question answering, and a Streamlit frontend turns it into a per-user "chat with your documents" experience with source citations attached to every answer.

## Features

- **Auth** — email/password signup and login, JWT bearer tokens, Argon2 password hashing
- **Multi-document, per-user library** — upload as many PDFs/TXT files as you want; each user only ever sees and queries their own documents
- **Grounded Q&A** — every answer is generated only from the retrieved chunks of the selected document, with the source passages and similarity scores shown alongside the answer
- **Automatic model failover** — if the primary Gemini model is overloaded, generation transparently falls back to a lighter model instead of failing the request
- **Delete support** — removing a document cleans up both the database row and its vectors in the vector store

## Architecture

```
Upload flow:
  file (.pdf/.txt) → extract text → chunk (250 words, 40-word overlap)
      → embed each chunk (gemini-embedding-2) → store in Chroma (scoped by user_id + document_id)

Ask flow:
  question → embed query → similarity search in Chroma (top-k, scoped to the selected document)
      → build context from retrieved chunks → generate_content (Gemini) → answer + sources
```

| Layer | Tech |
|---|---|
| API | FastAPI (async), Uvicorn |
| Database | PostgreSQL, SQLAlchemy (async ORM), Alembic migrations |
| Auth | JWT (python-jose), Argon2 (argon2-cffi) |
| Vector store | Chroma (persistent, local) |
| LLM / embeddings | Google Gemini API (`google-genai`) |
| PDF parsing | pdfplumber |
| Frontend | Streamlit |

## Project structure

```
.
├── main.py                  # FastAPI app entrypoint
├── database.py               # async engine/session setup
├── models.py                  # SQLAlchemy models (User, Document)
├── schemas.py                 # Pydantic request/response schemas
├── security.py                 # JWT + password hashing, get_current_user dependency
├── routers/
│   ├── auth.py                 # /auth/signup, /auth/login
│   └── documents.py            # /documents CRUD + /documents/{id}/ask
├── rag/
│   ├── chunker.py               # text → overlapping word-count chunks
│   ├── embedder.py              # Gemini embeddings (chunks + queries)
│   ├── vector_store.py          # Chroma wrapper (add/search/delete)
│   └── generator.py             # prompt construction + answer generation, with fallback
├── alembic/                    # database migrations
└── frontend/
    ├── app.py                   # Streamlit UI
    ├── api_client.py            # thin wrapper around the backend API
    └── requirements.txt
```

## Getting started

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (or pip, if you prefer to manage the venv yourself)
- A PostgreSQL database
- A [Gemini API key](https://aistudio.google.com/apikey)

### 1. Backend setup

Clone the repo and install dependencies:

```bash
uv sync
```

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/docuchat
SECRET_KEY=your-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
GEMINI_API_KEY=your-gemini-api-key
```

Run the database migrations:

```bash
uv run alembic upgrade head
```

Start the API:

```bash
uv run fastapi dev main.py
```

The API will be live at `http://localhost:8000` (interactive docs at `/docs`).

### 2. Frontend setup

In a separate terminal:

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

By default the frontend points at `http://localhost:8000`. To point it elsewhere:

```bash
DOCUCHAT_API_URL=http://your-host:8000 streamlit run app.py
```

Open `http://localhost:8501`, sign up, upload a document, and start asking questions.

## API reference

All `/documents/*` routes require an `Authorization: Bearer <token>` header.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/signup` | Create an account |
| `POST` | `/auth/login` | Log in, returns a JWT |
| `GET` | `/documents/` | List the current user's documents |
| `POST` | `/documents/upload` | Upload a PDF/TXT file — chunks, embeds, and indexes it |
| `GET` | `/documents/{id}` | Fetch a single document |
| `DELETE` | `/documents/{id}` | Delete a document and its indexed vectors |
| `POST` | `/documents/{id}/ask` | Ask a question about a document; returns an answer + cited sources |

> **Note:** `POST /documents/` (plain JSON create, no file) exists but does **not** chunk or embed the content — it's not wired into the RAG pipeline. Use `/documents/upload` for anything you want to be able to query.

## Known limitations

- **Session doesn't survive a browser refresh** — the JWT lives in Streamlit's `session_state`. Fine for local use; for persistence, swap in a cookie-backed store (e.g. `streamlit-cookies-controller`).
- **Chat history is in-memory only** — not persisted server-side, so it resets on refresh or restart.
- **Single collection vector store** — Chroma runs as a local persistent client; scoping is done via metadata filters (`user_id`, `document_id`) rather than separate collections per user.

## Roadmap

- [ ] Persist chat history server-side
- [ ] Cookie-based session persistence in the frontend
- [ ] Dockerize backend + frontend + Postgres with `docker-compose`
- [ ] Move model names to environment variables for easier migration
- [ ] Re-ranking of retrieved chunks before generation

