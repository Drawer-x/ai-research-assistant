import json
import re

from .embedding_service import get_embedding
from .llm_client import chat_with_deepseek
from .vector_store import search_similar_chunks


def _mock_answer() -> dict:
    return {
        "answer": "这是基于论文内容生成的占位回答。",
        "evidence": [],
        "has_evidence": False,
        "is_mock": True,
    }


def answer_question_about_paper(question: str, paper_text: str, paper_id: int | None = None) -> dict:
    """Answer from the RAG index when available, otherwise return the Sprint 1 mock."""
    try:
        if paper_id is None:
            return _mock_answer()
        query_embedding = get_embedding(question)
        chunks = search_similar_chunks(paper_id, query_embedding, top_k=8)
        context = "\n\n".join(chunks)
        prompt = f'''你是一名科研论文阅读助手。请严格根据下面内容回答问题，不允许编造。
返回 JSON：{{"answer":"","evidence":[]}}
论文相关内容：{context}
用户问题：{question}'''
        result = chat_with_deepseek(prompt)
        cleaned = re.sub(r"```json|```", "", result).strip()
        try:
            data = json.loads(cleaned)
        except Exception:
            data = {"answer": result, "evidence": chunks}
        data.setdefault("answer", "论文未提及")
        data.setdefault("evidence", chunks)
        data["has_evidence"] = bool(data["evidence"])
        data["is_mock"] = False
        return data
    except Exception:
        return _mock_answer()
