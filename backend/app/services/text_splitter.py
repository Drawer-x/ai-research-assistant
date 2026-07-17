"""Dependency-free paper text splitting with bounded overlap."""


def split_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[str]:
    """Split text near sentence/paragraph boundaries without blank chunks."""
    if not isinstance(text, str):
        raise TypeError("text 必须是字符串")
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap 必须大于等于 0 且小于 chunk_size")

    chunks: list[str] = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        if end < text_length:
            minimum = start + max(1, chunk_size // 2)
            candidates = [text.rfind(mark, minimum, end) for mark in ("\n\n", "\n", "。", "！", "？", ". ", " ")]
            boundary = max(candidates, default=-1)
            if boundary >= minimum:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk.strip():
            chunks.append(chunk)
        next_start = end - overlap
        start = end if next_start <= start else next_start
    return chunks
