import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

EMBEDDING_MODEL = "gemini-embedding-2"
OUTPUT_DIMENSIONALITY = 768
MAX_RETRIES = 5
BASE_BACKOFF_SECONDS = 5


def get_client() -> genai.Client:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Check your .env file.")
    return genai.Client(api_key=api_key)


def _embed(client: genai.Client, prefixed_text: str) -> list[float]:
    """gemini-embedding-2 takes the task as an inline prompt prefix instead
    of a task_type config field — see prepare_query/prepare_document below."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            config = types.EmbedContentConfig(output_dimensionality=OUTPUT_DIMENSIONALITY)
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=prefixed_text,
                config=config,
            )
            return result.embeddings[0].values
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            wait = BASE_BACKOFF_SECONDS * attempt
            print(f"    Retry {attempt}/{MAX_RETRIES} after error: {e}. Waiting {wait}s...")
            time.sleep(wait)


def embed_query(client: genai.Client, question: str) -> list[float]:
    return _embed(client, f"task: question answering | query: {question}")


def embed_chunks(client: genai.Client, chunks: list[dict]) -> list[list[float]]:
    embeddings = []
    for i, chunk in enumerate(chunks):
        title = chunk.get("title", "none")
        embedding = _embed(client, f"title: {title} | text: {chunk['text']}")
        embeddings.append(embedding)
        if (i + 1) % 25 == 0 or (i + 1) == len(chunks):
            print(f"{i + 1}/{len(chunks)} chunks embedded")
        time.sleep(0.2)
    return embeddings