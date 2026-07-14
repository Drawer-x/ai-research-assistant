"""FAISS-backed per-paper vector storage."""

import pickle
from pathlib import Path

from app.core.config import BACKEND_DIR


VECTOR_DIR = BACKEND_DIR / "vector_db"


def _dependencies():
    try:
        import faiss
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("向量检索需要安装 faiss-cpu 和 numpy") from exc
    return faiss, np


def _paths(paper_id: int) -> tuple[Path, Path]:
    if paper_id <= 0:
        raise ValueError("paper_id 必须是正整数")
    return VECTOR_DIR / f"{paper_id}.index", VECTOR_DIR / f"{paper_id}.pkl"


def save_vector_store(paper_id: int, chunks: list[str], embeddings: list[list[float]]) -> None:
    if not chunks or not embeddings:
        raise ValueError("chunks 和 embeddings 不能为空")
    if len(chunks) != len(embeddings):
        raise ValueError("文本分块数与向量数不一致")

    faiss, np = _dependencies()
    vectors = np.asarray(embeddings, dtype="float32")
    if vectors.ndim != 2 or vectors.shape[1] == 0:
        raise ValueError("向量维度无效")

    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    index_path, data_path = _paths(paper_id)
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(index_path))
    with data_path.open("wb") as output:
        pickle.dump(chunks, output)


def search_similar_chunks(paper_id: int, query_embedding: list[float], top_k: int = 3) -> list[str]:
    faiss, np = _dependencies()
    index_path, data_path = _paths(paper_id)
    if not index_path.exists() or not data_path.exists():
        raise FileNotFoundError("该论文尚未生成向量索引")

    index = faiss.read_index(str(index_path))
    with data_path.open("rb") as source:
        chunks = pickle.load(source)
    if not chunks:
        return []

    query = np.asarray([query_embedding], dtype="float32")
    if query.ndim != 2 or query.shape[1] != index.d:
        raise ValueError("查询向量维度与索引不一致")
    limit = max(1, min(int(top_k), len(chunks)))
    _, indices = index.search(query, limit)
    return [chunks[index] for index in indices[0] if 0 <= index < len(chunks)]


def search_vector_store(paper_id: int, query_embedding: list[float], top_k: int = 5) -> list[str]:
    """Compatibility alias for older callers."""
    return search_similar_chunks(paper_id, query_embedding, top_k)
