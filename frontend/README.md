# DocuChat frontend

A Streamlit UI for the DocuChat FastAPI backend: sign up / log in, upload
PDF or TXT documents, and ask questions against them with cited source
passages.

## Run it

1. Make sure the DocuChat backend is running first (defaults to
   `http://localhost:8000`).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the app:
   ```bash
   streamlit run app.py
   ```
4. If your backend isn't on `localhost:8000`, either set an env var before
   launching:
   ```bash
   DOCUCHAT_API_URL=http://your-host:8000 streamlit run app.py
   ```
   or set it from the "Advanced: backend URL" expander on the login screen.

## What's here

- `app.py` — the whole UI: auth screen, sidebar document list + uploader,
  chat panel with source citations.
- `api_client.py` — a small `requests`-based wrapper around the backend API,
  kept separate from Streamlit so it's easy to test or reuse.
- `.streamlit/config.toml` — base theme (paper/ink palette); most of the
  actual styling is injected CSS in `app.py` for finer control (chat
  bubbles, the highlighter-style source cards, etc).

## Known limitations (matching the current backend)

- **Only `/documents/upload` is used.** The plain `POST /documents/` (JSON,
  no file) endpoint doesn't chunk/embed/index the content, so a document
  created that way wouldn't be answerable — the frontend intentionally
  doesn't expose it.
- **No delete.** There's no `DELETE /documents/{id}` endpoint yet, so
  there's nothing in the UI for it either.
- **Session doesn't survive a browser refresh.** The JWT is kept in
  Streamlit's `session_state`, which resets on refresh. Fine for local use;
  if you want persistence later, the cleanest fix is a small cookie
  component (e.g. `streamlit-cookies-controller`) storing the token instead
  of `session_state`.
- **Chat history is in-memory only**, per browser session — it isn't
  persisted server-side, so it's gone on refresh or restart. The backend
  doesn't currently have a chat-history table; that'd be the natural next
  addition if you want conversations to survive a refresh.

## Dockerizing later

Since you mentioned this is next: this app is a single stateless process
reading one env var (`DOCUCHAT_API_URL`), so it containerizes cleanly —
a plain `python:3.13-slim` base, `pip install -r requirements.txt`, then
`streamlit run app.py --server.port 8501 --server.address 0.0.0.0` is all
it needs. Happy to write that Dockerfile (and a `docker-compose.yml` tying
it to the backend + Postgres) whenever you're ready for it.
