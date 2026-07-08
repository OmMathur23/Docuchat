import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

EMBEDDING_MODEL = "gemini-embedding-001"
OUTPUT_DIMENSIONALITY = 768
MAX_RETRIES = 5
BASE_BACKOFF_SECONDS = 5


def get_client() -> genai.Client:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Check your .env file.")
    return genai.Client(api_key=api_key)


def embed_chunks(
    client: genai.Client,
    text: str,
    title: str | None = None,
    task_type: str = "retrieval_document",
) -> list[float]:
    """
    Embed a single piece of text, with retry/backoff for transient
    errors (rate limits, temporary server issues).

    task_type matters: Gemini's embedding model produces slightly
    different vectors depending on which side of the retrieval pair
    the text is playing - 'retrieval_document' for chunks being
    indexed, 'retrieval_query' for the question being asked.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            config = types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=OUTPUT_DIMENSIONALITY,
                title=title,
            )
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
                config=config,
            )
            return result.embeddings[0].values
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            wait = BASE_BACKOFF_SECONDS * attempt
            print(f"    Retry {attempt}/{MAX_RETRIES} after error: {e}. Waiting {wait}s...")
            time.sleep(wait)


