from google import genai
from google.genai import types

GENERATION_MODEL = "gemini-2.5-flash"

PROMPT_TEMPLATE = """You are answering questions about a document the user has uploaded, using ONLY the context provided below.

Rules:
- Answer using only the information in the context.
- If the context doesn't contain enough information to answer, say so clearly instead of guessing.
- Reference which source(s) the information came from when relevant, e.g. "(Source 2)".
- Keep the answer focused and clearly written.

Context:
{context}

Question: {question}

Answer:"""


def build_context(retrieved_chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        parts.append(f"[Source {i}]\n{chunk['text']}")
    return "\n\n".join(parts)


def generate_answer(client: genai.Client, question: str, retrieved_chunks: list[dict]) -> str:
    context = build_context(retrieved_chunks)
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)

    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
    )
    return response.text.strip()