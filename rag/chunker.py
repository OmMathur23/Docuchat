import re

CHUNK_SIZE_WORDS = 250
OVERLAP_WORDS = 40


def split_into_sentences(text: str) -> list[str]:
    """Fallback splitter, used only when a single block is itself
    larger than the chunk budget (e.g. a dense prose paragraph)."""
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ö])", text)
    return [s.strip() for s in sentences if s.strip()]


def split_into_blocks(text: str) -> list[str]:
    """
    Split on blank lines / newlines into paragraph-ish units.
    Works uniformly across prose, slide bullets, resume sections -
    anything with line breaks, which covers most real documents,
    unlike sentence-ending punctuation which slides and bullet
    lists often lack.
    """
    blocks = re.split(r"\n\s*\n|\n", text)
    return [b.strip() for b in blocks if b.strip()]


def _pack(units: list[str]) -> list[dict]:
    """Word-count pack a list of text units (blocks or sentences)
    into chunks with overlap."""
    chunks = []
    current: list[str] = []
    current_word_count = 0

    def flush():
        if current:
            chunks.append({"text": "\n".join(current)})

    for unit in units:
        unit_words = len(unit.split())
        current.append(unit)
        current_word_count += unit_words

        if current_word_count >= CHUNK_SIZE_WORDS:
            flush()
            overlap, overlap_count = [], 0
            for u in reversed(current):
                w = len(u.split())
                if overlap_count + w > OVERLAP_WORDS:
                    break
                overlap.insert(0, u)
                overlap_count += w
            current, current_word_count = overlap, overlap_count

    flush()
    return chunks


def chunk_text(text: str) -> list[dict]:
    blocks = split_into_blocks(text)

    # expand any oversized block into sentences in-place, so the
    # single _pack() pass handles everything uniformly
    units = []
    for block in blocks:
        if len(block.split()) > CHUNK_SIZE_WORDS:
            units.extend(split_into_sentences(block))
        else:
            units.append(block)

    return _pack(units)