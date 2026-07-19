"""Optional ECNU reranker used after broad vector recall."""

from dataclasses import dataclass
import json
from urllib.request import Request, urlopen

from app.core.config import settings


class RerankServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class RerankedDocument:
    text: str
    original_index: int
    score: float


def rerank_documents(query: str, documents: list[str], top_n: int = 8) -> list[RerankedDocument]:
    if not settings.ecnu_api_key:
        raise RerankServiceError("未配置 ECNU_API_KEY")
    if not documents:
        return []
    try:
        body = json.dumps(
            {
                "model": "ecnu-rerank",
                "query": query,
                "documents": documents,
                "top_n": min(max(1, top_n), len(documents)),
                "return_documents": False,
            }
        ).encode("utf-8")
        request = Request(
            f"{settings.ecnu_base_url.rstrip('/')}/rerank",
            data=body,
            headers={
                "Authorization": f"Bearer {settings.ecnu_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=settings.ai_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        items = payload.get("results")
        if not isinstance(items, list):
            raise RerankServiceError("重排服务返回结构不完整")
        results: list[RerankedDocument] = []
        for item in items:
            index = item.get("index") if isinstance(item, dict) else None
            score = item.get("relevance_score") if isinstance(item, dict) else None
            if not isinstance(index, int) or not 0 <= index < len(documents):
                raise RerankServiceError("重排服务返回了无效索引")
            results.append(RerankedDocument(documents[index], index, float(score)))
        return results
    except RerankServiceError:
        raise
    except Exception as exc:
        raise RerankServiceError("重排服务调用失败") from exc
