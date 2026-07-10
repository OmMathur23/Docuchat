import base64
import html
import json
import os
import time

import requests
import streamlit as st

from api_client import APIError, DocuChatClient

DEFAULT_API_URL = os.environ.get("DOCUCHAT_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="DocuChat",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --paper: #F7F6F2;
    --paper-dim: #EFEBE2;
    --ink: #1C1B1F;
    --ink-soft: #55524A;
    --rule: #D8D2C4;
    --highlighter: #F5C518;
    --highlighter-soft: #FBEEB8;
    --teal: #2F5D62;
    --teal-dark: #234548;
    --brick: #B3432B;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: var(--paper); color: var(--ink); }

h1, h2, h3 { font-family: 'Source Serif 4', serif !important; color: var(--ink) !important; letter-spacing: -0.01em; }

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: var(--paper-dim);
    border-right: 1px solid var(--rule);
}
[data-testid="stSidebar"] .stButton>button {
    width: 100%;
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    color: var(--ink);
    font-family: 'Inter', sans-serif;
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
}
[data-testid="stSidebar"] .stButton>button:hover {
    background: #E4DECF;
    border-color: var(--rule);
}

/* Primary buttons everywhere */
.stButton>button[kind="primary"], .stFormSubmitButton>button {
    background-color: var(--teal) !important;
    color: var(--paper) !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}
.stButton>button[kind="primary"]:hover, .stFormSubmitButton>button:hover {
    background-color: var(--teal-dark) !important;
}

/* Chat bubbles */
[data-testid="stChatMessage"] {
    background: #FFFFFF;
    border: 1px solid var(--rule);
    border-radius: 10px;
    padding: 0.25rem 0.5rem;
}

/* Chat input */
[data-testid="stChatInput"] textarea {
    font-family: 'Inter', sans-serif;
}

/* Source / evidence cards — the signature element */
.source-card {
    border-left: 4px solid var(--highlighter);
    background: linear-gradient(90deg, var(--highlighter-soft) 0%, #FFFFFF 18%);
    padding: 0.6rem 0.9rem;
    margin-bottom: 0.5rem;
    border-radius: 0 6px 6px 0;
}
.source-card .source-meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--ink-soft);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.2rem;
}
.source-card .source-text {
    font-size: 0.88rem;
    color: var(--ink);
    line-height: 1.45;
}

/* Doc list "shelf" cards */
.doc-card {
    border: 1px solid var(--rule);
    border-radius: 6px;
    padding: 0.5rem 0.7rem;
    margin-bottom: 0.35rem;
    font-size: 0.85rem;
}
.doc-card.selected {
    border-color: var(--teal);
    background: #E7F0EF;
}

/* Auth card */
.auth-wrap { max-width: 420px; margin: 4rem auto 0 auto; }
.auth-title { font-family: 'Source Serif 4', serif; font-size: 2rem; margin-bottom: 0.1rem; }
.auth-sub { color: var(--ink-soft); margin-bottom: 1.6rem; }

/* Empty state */
.empty-state {
    text-align: center;
    color: var(--ink-soft);
    padding: 5rem 1rem;
    font-family: 'Source Serif 4', serif;
    font-size: 1.3rem;
}

hr { border-color: var(--rule) !important; }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------

def init_state():
    defaults = {
        "api_url": DEFAULT_API_URL,
        "token": None,
        "user_id": None,
        "auth_mode": "login",  # or "signup"
        "documents": [],
        "selected_doc_id": None,
        "chat_histories": {},  # {doc_id: [ {role, content, sources?} ]}
        "auth_error": None,
        "auth_notice": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


def client() -> DocuChatClient:
    return DocuChatClient(st.session_state.api_url, st.session_state.token)


def decode_user_id(token: str) -> str | None:
    """Best-effort, unverified decode of the JWT payload just to show
    'Signed in as User #N' — the backend already verifies the signature
    on every real request, this is purely cosmetic."""
    try:
        payload_b64 = token.split(".")[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        return payload.get("sub")
    except Exception:
        return None


def refresh_documents():
    try:
        st.session_state.documents = client().list_documents()
    except APIError as e:
        if e.status_code == 401:
            handle_session_expired()
        else:
            st.error(f"Couldn't load documents: {e.detail}")
    except requests.exceptions.ConnectionError:
        st.error(f"Can't reach the backend at {st.session_state.api_url}. Is it running?")


def handle_session_expired():
    st.session_state.token = None
    st.session_state.user_id = None
    st.session_state.auth_notice = "Your session expired. Please log in again."
    st.rerun()


def sign_out():
    st.session_state.token = None
    st.session_state.user_id = None
    st.session_state.documents = []
    st.session_state.selected_doc_id = None
    st.session_state.chat_histories = {}
    st.rerun()


# --------------------------------------------------------------------------
# Auth screen
# --------------------------------------------------------------------------

def render_auth():
    st.markdown('<div class="auth-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">📖 DocuChat</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="auth-sub">Upload a document, ask it questions, get answers with the exact passages they came from.</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.auth_notice:
        st.warning(st.session_state.auth_notice)
        st.session_state.auth_notice = None

    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)
        if submitted:
            if not email or not password:
                st.error("Enter both email and password.")
            else:
                try:
                    result = client().login(email, password)
                    st.session_state.token = result["access_token"]
                    st.session_state.user_id = decode_user_id(st.session_state.token)
                    refresh_documents()
                    st.rerun()
                except APIError as e:
                    st.error(e.detail)
                except requests.exceptions.ConnectionError:
                    st.error(f"Can't reach the backend at {st.session_state.api_url}. Is it running?")

    with tab_signup:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            password2 = st.text_input("Confirm password", type="password", key="signup_password2")
            submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
        if submitted:
            if not email or not password:
                st.error("Enter both email and password.")
            elif password != password2:
                st.error("Passwords don't match.")
            else:
                try:
                    client().signup(email, password)
                    st.success("Account created. Log in from the other tab.")
                except APIError as e:
                    st.error(e.detail)
                except requests.exceptions.ConnectionError:
                    st.error(f"Can't reach the backend at {st.session_state.api_url}. Is it running?")

    with st.expander("Advanced: backend URL"):
        st.session_state.api_url = st.text_input("API base URL", value=st.session_state.api_url)

    st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Sidebar: document shelf + upload
# --------------------------------------------------------------------------

@st.dialog("Delete document?")
def confirm_delete_dialog(doc_id: int, title: str):
    st.write(f"Delete **{title}**? This removes it and everything it learned — permanently.")
    col_cancel, col_delete = st.columns(2)
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    with col_delete:
        if st.button("Delete", type="primary", use_container_width=True):
            try:
                client().delete_document(doc_id)
                st.session_state.chat_histories.pop(doc_id, None)
                if st.session_state.selected_doc_id == doc_id:
                    st.session_state.selected_doc_id = None
                refresh_documents()
                st.rerun()
            except APIError as e:
                if e.status_code == 401:
                    handle_session_expired()
                else:
                    st.error(e.detail)
            except requests.exceptions.ConnectionError:
                st.error(f"Can't reach the backend at {st.session_state.api_url}.")


def render_sidebar():
    with st.sidebar:
        st.markdown("### 📖 DocuChat")
        st.caption(f"Signed in as User #{st.session_state.user_id}")
        if st.button("Log out", use_container_width=True):
            sign_out()

        st.divider()
        st.markdown("**Upload a document**")
        uploaded = st.file_uploader(
            "PDF or TXT", type=["pdf", "txt"], label_visibility="collapsed"
        )
        if uploaded is not None:
            if st.button("Upload & index", type="primary", use_container_width=True):
                with st.spinner("Reading and indexing your document — this can take a minute for longer files…"):
                    try:
                        new_doc = client().upload_document(
                            uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream"
                        )
                        refresh_documents()
                        st.session_state.selected_doc_id = new_doc["id"]
                        st.success(f"Indexed “{new_doc['title']}”")
                        time.sleep(0.6)
                        st.rerun()
                    except APIError as e:
                        if e.status_code == 401:
                            handle_session_expired()
                        else:
                            st.error(e.detail)
                    except requests.exceptions.ConnectionError:
                        st.error(f"Can't reach the backend at {st.session_state.api_url}.")

        st.divider()
        st.markdown("**Your documents**")

        if not st.session_state.documents:
            st.caption("No documents yet — upload one above to get started.")
        else:
            for doc in st.session_state.documents:
                is_selected = doc["id"] == st.session_state.selected_doc_id
                label = f"{'📄 ' if not is_selected else '📖 '}{doc['title']}"
                col_select, col_delete = st.columns([5, 1])
                with col_select:
                    if st.button(label, key=f"doc_{doc['id']}", use_container_width=True):
                        st.session_state.selected_doc_id = doc["id"]
                        st.rerun()
                with col_delete:
                    if st.button("🗑", key=f"del_{doc['id']}", use_container_width=True):
                        confirm_delete_dialog(doc["id"], doc["title"])


# --------------------------------------------------------------------------
# Main: chat panel
# --------------------------------------------------------------------------

def render_source_card(source: dict):
    similarity_pct = round(source.get("similarity", 0) * 100)
    section = html.escape(str(source.get("section", "unknown")))
    text = html.escape(source.get("text", "")).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="source-card">
            <div class="source-meta">Section: {section} · {similarity_pct}% match</div>
            <div class="source-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat():
    doc_id = st.session_state.selected_doc_id

    if doc_id is None:
        st.markdown(
            '<div class="empty-state">Select a document on the left, or upload a new one, to start asking questions.</div>',
            unsafe_allow_html=True,
        )
        return

    doc = next((d for d in st.session_state.documents if d["id"] == doc_id), None)
    if doc is None:
        st.session_state.selected_doc_id = None
        st.rerun()
        return

    st.markdown(f"## {doc['title']}")
    history = st.session_state.chat_histories.setdefault(doc_id, [])

    for turn in history:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])
            if turn.get("sources"):
                with st.expander(f"📎 {len(turn['sources'])} source(s) referenced"):
                    for source in turn["sources"]:
                        render_source_card(source)

    question = st.chat_input(f"Ask something about “{doc['title']}”…")
    if question:
        history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching the document and thinking…"):
                try:
                    result = client().ask(doc_id, question)
                    answer = result["answer"]
                    sources = result.get("sources", [])
                    st.markdown(answer)
                    if sources:
                        with st.expander(f"📎 {len(sources)} source(s) referenced"):
                            for source in sources:
                                render_source_card(source)
                    history.append({"role": "assistant", "content": answer, "sources": sources})
                except APIError as e:
                    if e.status_code == 401:
                        handle_session_expired()
                    else:
                        err_msg = f"Something went wrong: {e.detail}"
                        st.error(err_msg)
                        history.append({"role": "assistant", "content": err_msg})
                except requests.exceptions.ConnectionError:
                    err_msg = f"Can't reach the backend at {st.session_state.api_url}."
                    st.error(err_msg)
                    history.append({"role": "assistant", "content": err_msg})


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

if not st.session_state.token:
    render_auth()
else:
    if not st.session_state.documents:
        refresh_documents()
    render_sidebar()
    render_chat()
