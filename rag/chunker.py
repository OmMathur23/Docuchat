import re
CHUNK_SIZE_WORDS = 250
OVERLAP_WORDS = 40

def split_into_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ö])", text)
    return [s.strip() for s in sentences if s.strip()]

def chunk_text(text:str)-> list[dict]:
    sentences = split_into_sentences(text)
    chunks = []

    current_sentences: list[str] = []
    current_word_count = 0

    def flush_chunk():
        if not current_sentences:
            return
        chunk_text = " ".join(current_sentences)
        chunks.append({
            "text": chunk_text,
        })

    for sentence in sentences:
        current_sentences.append(sentence)
        current_word_count += len(sentence.split())

        if current_word_count >= CHUNK_SIZE_WORDS:
            flush_chunk()
            overlap_sentences = []
            overlap_count = 0
            for s in reversed(current_sentences):
                w = len(s.split())
                if overlap_count + w > OVERLAP_WORDS:
                    break
                overlap_sentences.insert(0,s)
                overlap_count += w
            
            current_sentences = overlap_sentences
            current_word_count = overlap_count

    flush_chunk()
    return chunks
