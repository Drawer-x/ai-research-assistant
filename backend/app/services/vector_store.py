"""Failure-safe FAISS-backed per-paper vector storage."""
from __future__ import annotations

import math
import os
import pickle
from contextlib import contextmanager
from hashlib import sha256
from dataclasses import dataclass
from pathlib import Path
from threading import Lock, RLock
from uuid import uuid4

from app.core.config import BACKEND_DIR


VECTOR_DIR = Path(os.environ.get("VECTOR_DIR") or (BACKEND_DIR / "vector_db"))
_LOCKS: dict[int, RLock] = {}
_LOCKS_GUARD = Lock()


class VectorStoreError(RuntimeError):
    """Base class for controlled vector-store failures."""


class VectorStoreNotFoundError(VectorStoreError, FileNotFoundError):
    pass


class VectorStoreCorruptError(VectorStoreError):
    pass


class VectorDimensionError(VectorStoreError, ValueError):
    pass


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    chunk_index: int
    score: float


class _MetadataUnpickler(pickle.Unpickler):
    """Load only pickle primitive containers; never import globals or callables."""

    def find_class(self, module: str, name: str):
        raise pickle.UnpicklingError("向量元数据包含不允许的全局对象")


def _load_metadata(source):
    return _MetadataUnpickler(source).load()


def _dependencies():
    try:
        import faiss
        import numpy as np
    except ImportError as exc:
        raise VectorStoreError("向量检索需要安装 faiss-cpu 和 numpy") from exc
    return faiss, np


def _paths(paper_id: int) -> tuple[Path, Path]:
    if isinstance(paper_id, bool) or not isinstance(paper_id, int) or paper_id <= 0:
        raise ValueError("paper_id 必须是正整数")
    return VECTOR_DIR / f"{paper_id}.index", VECTOR_DIR / f"{paper_id}.pkl"


def _paper_lock(paper_id: int) -> RLock:
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(paper_id, RLock())


@contextmanager
def _store_lock(paper_id: int):
    """Serialize same-paper readers and writers across threads and processes."""
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = VECTOR_DIR / f".{paper_id}.lock"
    with _paper_lock(paper_id), lock_path.open("a+b") as lock_file:
        if os.name == "nt":
            import msvcrt

            lock_file.seek(0, os.SEEK_END)
            if lock_file.tell() == 0:
                lock_file.write(b"\0")
                lock_file.flush()
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _source_digest(source_text: str) -> str:
    return sha256(source_text.encode("utf-8")).hexdigest()


def _validate_chunks(chunks: list[str]) -> None:
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("chunks 不能为空")
    if any(not isinstance(chunk, str) or not chunk.strip() for chunk in chunks):
        raise ValueError("chunks 不能包含空白或非字符串内容")


def _vectors_array(embeddings: list[list[float]], expected_count: int):
    if not isinstance(embeddings, list) or not embeddings:
        raise ValueError("embeddings 不能为空")
    if len(embeddings) != expected_count:
        raise ValueError("文本分块数与向量数不一致")
    _, np = _dependencies()
    try:
        vectors = np.asarray(embeddings, dtype="float32")
    except (TypeError, ValueError) as exc:
        raise VectorDimensionError("向量维度不一致或内容无效") from exc
    if vectors.ndim != 2 or vectors.shape[1] == 0:
        raise VectorDimensionError("向量维度无效")
    if not np.isfinite(vectors).all():
        raise VectorDimensionError("向量包含非有限数值")
    return vectors


def _replace_pair(index_tmp: Path, data_tmp: Path, index_path: Path, data_path: Path) -> None:
    token = uuid4().hex
    backups: list[tuple[Path, Path]] = []
    replaced_targets: list[Path] = []
    try:
        for target in (index_path, data_path):
            if target.exists():
                backup = target.with_name(f".{target.name}.{token}.bak")
                os.replace(target, backup)
                backups.append((target, backup))
        os.replace(index_tmp, index_path)
        replaced_targets.append(index_path)
        os.replace(data_tmp, data_path)
        replaced_targets.append(data_path)
    except Exception:
        for target in replaced_targets:
            if target.exists():
                target.unlink(missing_ok=True)
        for original, backup in reversed(backups):
            if original.exists():
                original.unlink(missing_ok=True)
            if backup.exists():
                os.replace(backup, original)
        raise
    else:
        for _, backup in backups:
            backup.unlink(missing_ok=True)


def save_vector_store(
    paper_id: int,
    chunks: list[str],
    embeddings: list[list[float]],
    *,
    owner_id: int | None = None,
    source_text: str | None = None,
) -> None:
    """Validate and replace the index/data pair without half-written outputs."""
    index_path, data_path = _paths(paper_id)
    if owner_id is not None and (
        isinstance(owner_id, bool) or not isinstance(owner_id, int) or owner_id <= 0
    ):
        raise ValueError("owner_id 必须是正整数")
    if source_text is not None and not isinstance(source_text, str):
        raise TypeError("source_text 必须是字符串")
    _validate_chunks(chunks)
    vectors = _vectors_array(embeddings, len(chunks))
    faiss, _ = _dependencies()
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    token = uuid4().hex
    index_tmp = VECTOR_DIR / f".{paper_id}.{token}.index.tmp"
    data_tmp = VECTOR_DIR / f".{paper_id}.{token}.pkl.tmp"
    payload = {
        "version": 2,
        "paper_id": paper_id,
        "owner_id": owner_id,
        "source_sha256": _source_digest(source_text) if source_text is not None else None,
        "chunks": chunks,
    }
    with _store_lock(paper_id):
        try:
            index = faiss.IndexFlatL2(vectors.shape[1])
            index.add(vectors)
            faiss.write_index(index, str(index_tmp))
            with data_tmp.open("wb") as output:
                pickle.dump(payload, output, protocol=pickle.HIGHEST_PROTOCOL)
                output.flush()
                os.fsync(output.fileno())
            _replace_pair(index_tmp, data_tmp, index_path, data_path)
        finally:
            index_tmp.unlink(missing_ok=True)
            data_tmp.unlink(missing_ok=True)


def _load_store(
    paper_id: int,
    *,
    owner_id: int | None = None,
    source_text: str | None = None,
):
    index_path, data_path = _paths(paper_id)
    with _store_lock(paper_id):
        if not index_path.exists() and not data_path.exists():
            raise VectorStoreNotFoundError("该论文尚未生成向量索引")
        if not index_path.exists() or not data_path.exists():
            raise VectorStoreCorruptError("向量索引文件不完整，需要重建")
        faiss, _ = _dependencies()
        try:
            index = faiss.read_index(str(index_path))
            with data_path.open("rb") as source:
                payload = _load_metadata(source)
        except Exception as exc:
            raise VectorStoreCorruptError("向量索引损坏或不兼容，需要重建") from exc
        chunks = payload.get("chunks") if isinstance(payload, dict) else payload
        if owner_id is not None or source_text is not None:
            if not isinstance(payload, dict) or payload.get("version") != 2:
                raise VectorStoreCorruptError("旧索引缺少归属信息，需要重建")
            if payload.get("paper_id") != paper_id:
                raise VectorStoreCorruptError("向量索引论文标识不匹配，需要重建")
            if owner_id is not None and payload.get("owner_id") != owner_id:
                raise VectorStoreCorruptError("向量索引归属不匹配，需要重建")
            if source_text is not None and payload.get("source_sha256") != _source_digest(source_text):
                raise VectorStoreCorruptError("向量索引与当前论文内容不匹配，需要重建")
        if not isinstance(chunks, list) or any(not isinstance(chunk, str) for chunk in chunks):
            raise VectorStoreCorruptError("向量索引元数据损坏，需要重建")
        if index.ntotal != len(chunks):
            raise VectorStoreCorruptError("向量数量与文本分块数不一致，需要重建")
        if index.d <= 0:
            raise VectorStoreCorruptError("向量索引维度无效，需要重建")
        if getattr(index, "metric_type", faiss.METRIC_L2) != faiss.METRIC_L2:
            raise VectorStoreCorruptError("向量索引距离类型不兼容，需要重建")
    return index, chunks


def validate_vector_store(
    paper_id: int,
    *,
    owner_id: int | None = None,
    source_text: str | None = None,
) -> None:
    """Validate existence, integrity and optional paper identity before embedding."""
    _load_store(paper_id, owner_id=owner_id, source_text=source_text)


def search_similar_chunks_with_scores(
    paper_id: int,
    query_embedding: list[float],
    top_k: int = 3,
    *,
    owner_id: int | None = None,
    source_text: str | None = None,
) -> list[RetrievedChunk]:
    """Return traceable L2 retrieval results while supporting old indexes."""
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k 必须是正整数")
    index, chunks = _load_store(paper_id, owner_id=owner_id, source_text=source_text)
    if not chunks:
        return []
    _, np = _dependencies()
    try:
        query = np.asarray([query_embedding], dtype="float32")
    except (TypeError, ValueError) as exc:
        raise VectorDimensionError("查询向量内容无效") from exc
    if query.ndim != 2 or query.shape[1] != index.d:
        raise VectorDimensionError("查询向量维度与索引不一致")
    if not np.isfinite(query).all():
        raise VectorDimensionError("查询向量包含非有限数值")
    limit = min(top_k, len(chunks))
    distances, indices = index.search(query, limit)
    results: list[RetrievedChunk] = []
    for distance, chunk_index in zip(distances[0], indices[0]):
        index_value = int(chunk_index)
        score = float(distance)
        if 0 <= index_value < len(chunks) and math.isfinite(score):
            results.append(RetrievedChunk(chunks[index_value], index_value, score))
    return results


def search_similar_chunks(
    paper_id: int,
    query_embedding: list[float],
    top_k: int = 3,
    *,
    owner_id: int | None = None,
    source_text: str | None = None,
) -> list[str]:
    """Backward-compatible public helper returning only evidence strings."""
    return [
        item.text
        for item in search_similar_chunks_with_scores(
            paper_id,
            query_embedding,
            top_k,
            owner_id=owner_id,
            source_text=source_text,
        )
    ]


def search_vector_store(paper_id: int, query_embedding: list[float], top_k: int = 5) -> list[str]:
    """Compatibility alias for older callers."""
    return search_similar_chunks(paper_id, query_embedding, top_k)


def delete_vector_store(
    paper_id: int,
    *,
    owner_id: int | None = None,
    source_text: str | None = None,
) -> None:
    """Remove an index pair, optionally only when its identity still matches."""
    index_path, data_path = _paths(paper_id)
    with _store_lock(paper_id):
        if (owner_id is not None or source_text is not None) and data_path.exists():
            try:
                with data_path.open("rb") as source:
                    payload = _load_metadata(source)
            except Exception:
                return
            if not isinstance(payload, dict) or payload.get("version") != 2:
                return
            if owner_id is not None and payload.get("owner_id") != owner_id:
                return
            if source_text is not None and payload.get("source_sha256") != _source_digest(source_text):
                return
        index_path.unlink(missing_ok=True)
        data_path.unlink(missing_ok=True)
