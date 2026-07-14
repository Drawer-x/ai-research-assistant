"""
论文文本切分
"""


def split_text(
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
):
    """
    将论文切分成多个chunk

    chunk_size:
        每个片段长度

    overlap:
        重叠区域，避免语义断裂
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap 必须大于等于 0 且小于 chunk_size")

    chunks = []

    start = 0

    text_length = len(text)


    while start < text_length:

        end = start + chunk_size

        chunk = text[start:end]


        if chunk.strip():
            chunks.append(chunk)


        start = end - overlap


    return chunks
