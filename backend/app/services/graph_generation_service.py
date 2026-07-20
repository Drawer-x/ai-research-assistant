"""Deterministic, database-free literature relation generation."""

from __future__ import annotations

import logging
import re
from itertools import combinations, permutations
from typing import Any

logger = logging.getLogger(__name__)

ALLOWED_RELATION_TYPES = {"citation", "topic_similarity", "method_similarity"}
RELATION_ORDER = {"citation": 0, "topic_similarity": 1, "method_similarity": 2}
MAX_PAPERS = 200
MAX_ABSTRACT_CHARS = 3_000
MAX_FULL_TEXT_CHARS = 12_000

_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "in", "is", "it", "model", "models", "of", "on", "or", "paper",
    "research", "result", "results", "study", "the", "this", "to", "using",
    "we", "with", "一种", "以及", "使用", "分析", "基于", "实验", "方法",
    "本文", "模型", "结果", "研究", "论文", "通过",
}
_GENERIC_TITLES = {"introduction", "overview", "survey", "review", "研究综述", "综述"}

_METHOD_PATTERNS: dict[str, tuple[str, ...]] = {
    "Transformer": ("transformer", "变换器"),
    "自注意力": ("self attention", "self-attention", "自注意力"),
    "注意力机制": ("attention mechanism", "注意力机制"),
    "CNN": ("cnn", "convolutional neural network", "卷积神经网络"),
    "RNN": ("rnn", "recurrent neural network", "循环神经网络"),
    "LSTM": ("lstm", "long short term memory", "长短期记忆"),
    "GRU": ("gru", "gated recurrent unit", "门控循环单元"),
    "BERT": ("bert",),
    "RAG": ("rag", "retrieval augmented generation", "检索增强生成"),
    "知识图谱": ("knowledge graph", "知识图谱"),
    "图神经网络": ("graph neural network", "gnn", "图神经网络"),
    "对比学习": ("contrastive learning", "对比学习"),
    "微调": ("fine tuning", "fine-tuning", "finetuning", "微调"),
    "提示学习": ("prompt learning", "提示学习"),
    "LoRA": ("lora", "low rank adaptation", "低秩适配"),
    "Embedding": ("embedding", "embeddings", "嵌入表示", "向量嵌入"),
    "向量检索": ("vector retrieval", "vector search", "向量检索"),
    "强化学习": ("reinforcement learning", "强化学习"),
    "扩散模型": ("diffusion model", "diffusion models", "扩散模型"),
    "自编码器": ("autoencoder", "auto encoder", "自编码器"),
    "随机森林": ("random forest", "随机森林"),
    "SVM": ("svm", "support vector machine", "支持向量机"),
    "XGBoost": ("xgboost",),
}


def _safe_text(value: Any, limit: int) -> str:
    return re.sub(r"\s+", " ", value).strip()[:limit] if isinstance(value, str) else ""


def _bounded_full_text(value: Any) -> str:
    """Keep both the paper body opening and its likely reference-section tail."""
    if not isinstance(value, str):
        return ""
    stripped = value.strip()
    if len(stripped) <= MAX_FULL_TEXT_CHARS:
        return re.sub(r"\s+", " ", stripped)
    head_size = MAX_FULL_TEXT_CHARS // 2
    tail_size = MAX_FULL_TEXT_CHARS - head_size - 1
    head = re.sub(r"\s+", " ", stripped[:head_size]).strip()
    tail = re.sub(r"\s+", " ", stripped[-tail_size:]).strip()
    return f"{head}\n{tail}"


def _normalize_search_text(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", value.casefold()).strip()


def _text_tokens(text: str) -> set[str]:
    normalized = _normalize_search_text(text)
    english = re.findall(r"[a-z0-9][a-z0-9+#.-]{1,}", text.casefold())
    chinese: set[str] = set()
    for phrase in re.findall(r"[\u4e00-\u9fff]{2,}", normalized):
        for width in range(2, min(4, len(phrase)) + 1):
            chinese.update(
                phrase[index:index + width]
                for index in range(len(phrase) - width + 1)
            )
    return {
        token for token in (*english, *chinese)
        if token not in _STOP_WORDS and len(token) >= 2
    }


def _normalize_papers(papers: Any) -> list[dict[str, Any]] | None:
    if not isinstance(papers, list) or not 2 <= len(papers) <= MAX_PAPERS:
        return None
    normalized: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for paper in papers:
        if not isinstance(paper, dict):
            return None
        paper_id = paper.get("paper_id")
        if (
            isinstance(paper_id, bool)
            or not isinstance(paper_id, int)
            or paper_id <= 0
            or paper_id in seen_ids
        ):
            return None
        seen_ids.add(paper_id)
        normalized.append(
            {
                "paper_id": paper_id,
                "title": _safe_text(paper.get("title"), 500),
                "authors": _safe_text(paper.get("authors"), 1_000),
                "year": (
                    paper.get("year")
                    if isinstance(paper.get("year"), int) and not isinstance(paper.get("year"), bool)
                    else None
                ),
                "venue": _safe_text(paper.get("venue"), 300),
                "abstract": _safe_text(paper.get("abstract"), MAX_ABSTRACT_CHARS),
                "full_text": _bounded_full_text(paper.get("full_text")),
            }
        )
    return sorted(normalized, key=lambda item: item["paper_id"])


def _weighted_tokens(paper: dict[str, Any]) -> dict[str, float]:
    fields = (
        (paper["title"], 4.0),
        (paper["abstract"], 2.5),
        (paper["authors"], 0.4),
        (paper["venue"], 0.4),
        (paper["full_text"][:4_000], 1.0),
    )
    weights: dict[str, float] = {}
    for text, weight in fields:
        for token in _text_tokens(text):
            weights[token] = max(weights.get(token, 0.0), weight)
    return weights


def _weighted_jaccard(
    source: dict[str, float], target: dict[str, float]
) -> tuple[set[str], float]:
    common = source.keys() & target.keys()
    union = source.keys() | target.keys()
    if not union:
        return set(), 0.0
    numerator = sum(min(source[token], target[token]) for token in common)
    denominator = sum(
        max(source.get(token, 0.0), target.get(token, 0.0)) for token in union
    )
    return set(common), numerator / denominator if denominator else 0.0


def _display_keywords(
    common: set[str],
    source: dict[str, float],
    target: dict[str, float],
    limit: int = 3,
) -> list[str]:
    ranked = sorted(
        common,
        key=lambda token: (-min(source[token], target[token]), -len(token), token),
    )
    selected: list[str] = []
    for token in ranked:
        if any(token in existing or existing in token for existing in selected):
            continue
        selected.append(token)
        if len(selected) >= limit:
            break
    return selected


def _undirected_relation(
    first: dict[str, Any],
    second: dict[str, Any],
    relation_type: str,
    weight: float,
    description: str,
) -> dict[str, Any]:
    source, target = sorted((first["paper_id"], second["paper_id"]))
    return {
        "source": source,
        "target": target,
        "relation_type": relation_type,
        "weight": round(min(1.0, max(0.0, float(weight))), 3),
        "description": description,
        "is_mock": False,
    }


def _topic_relation(first: dict[str, Any], second: dict[str, Any]) -> dict | None:
    first_tokens = _weighted_tokens(first)
    second_tokens = _weighted_tokens(second)
    common, score = _weighted_jaccard(first_tokens, second_tokens)
    same_title = bool(first["title"]) and (
        _normalize_search_text(first["title"])
        == _normalize_search_text(second["title"])
    )
    if not same_title and (len(common) < 2 or score < 0.08):
        return None
    keywords = _display_keywords(common, first_tokens, second_tokens)
    if same_title:
        description = "两篇论文标题相同，主题高度一致。"
        weight = 1.0
    else:
        description = f"两篇论文的真实文本共同涉及{'、'.join(keywords)}。"
        weight = min(0.95, max(0.1, score))
    return _undirected_relation(first, second, "topic_similarity", weight, description)


def _method_set(paper: dict[str, Any]) -> set[str]:
    text = _normalize_search_text(
        " ".join((paper["title"], paper["abstract"], paper["full_text"][:4_000]))
    )
    methods: set[str] = set()
    for method, variants in _METHOD_PATTERNS.items():
        for variant in variants:
            normalized_variant = _normalize_search_text(variant)
            if normalized_variant and re.search(
                rf"(?<![a-z0-9]){re.escape(normalized_variant)}(?![a-z0-9])", text
            ):
                methods.add(method)
                break
    return methods


def _method_relation(first: dict[str, Any], second: dict[str, Any]) -> dict | None:
    first_methods, second_methods = _method_set(first), _method_set(second)
    common = first_methods & second_methods
    if not common:
        return None
    union = first_methods | second_methods
    overlap = len(common) / len(union)
    weight = min(0.98, 0.55 + 0.4 * overlap + 0.02 * (len(common) - 1))
    return _undirected_relation(
        first,
        second,
        "method_similarity",
        weight,
        f"两篇论文共同采用{'、'.join(sorted(common))}方法。",
    )


def _title_is_specific(title: str) -> bool:
    normalized = _normalize_search_text(title)
    if not normalized or normalized in _GENERIC_TITLES:
        return False
    english_words = re.findall(r"[a-z0-9]+", normalized)
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", normalized)
    return len(english_words) >= 3 or len(chinese_chars) >= 6


def _reference_section(full_text: str) -> str:
    lowered = full_text.casefold()
    positions = [
        lowered.rfind(marker)
        for marker in ("references", "bibliography", "参考文献", "引用文献")
    ]
    start = max(positions, default=-1)
    return full_text[start:] if start >= 0 else ""


def _author_markers(authors: str) -> list[str]:
    markers: set[str] = set()
    for group in re.split(r"[,;，；]|\band\b", authors, flags=re.IGNORECASE):
        group = group.strip()
        if not group or group.casefold() in {"et al", "et al."}:
            continue
        english = re.findall(r"[A-Za-z][A-Za-z'-]+", group)
        chinese = re.findall(r"[\u4e00-\u9fff]{2,4}", group)
        if english and len(english[-1]) >= 3:
            markers.add(english[-1].casefold())
        markers.update(chinese)
    return sorted(markers)


def _directed_citation(
    source: dict[str, Any], target: dict[str, Any], weight: float, description: str
) -> dict[str, Any]:
    return {
        "source": source["paper_id"],
        "target": target["paper_id"],
        "relation_type": "citation",
        "weight": round(min(1.0, max(0.0, float(weight))), 3),
        "description": description,
        "is_mock": False,
    }


def _citation_relation(source: dict[str, Any], target: dict[str, Any]) -> dict | None:
    target_title = target["title"]
    if not _title_is_specific(target_title) or not source["full_text"]:
        return None
    normalized_title = _normalize_search_text(target_title)
    normalized_body = _normalize_search_text(source["full_text"])
    references = _reference_section(source["full_text"])
    normalized_references = _normalize_search_text(references)
    source_name = source["title"] or f"论文 {source['paper_id']}"
    target_name = target_title or f"论文 {target['paper_id']}"

    if normalized_references and normalized_title in normalized_references:
        return _directed_citation(
            source, target, 0.96,
            f"《{source_name}》的参考文献区域出现了《{target_name}》的完整标题。",
        )
    if normalized_title in normalized_body:
        return _directed_citation(
            source, target, 0.85,
            f"《{source_name}》正文出现了《{target_name}》的完整标题。",
        )

    year = str(target["year"]) if target["year"] is not None else ""
    author_markers = _author_markers(target["authors"])
    title_tokens = {
        token for token in _text_tokens(target_title)
        if len(token) >= 3 and token not in _STOP_WORDS
    }
    common_keywords = title_tokens & _text_tokens(source["full_text"])
    evidence_text = normalized_references or normalized_body
    has_author = any(marker in evidence_text for marker in author_markers)
    if year and year in evidence_text and has_author and len(common_keywords) >= 2:
        return _directed_citation(
            source, target, 0.68 if normalized_references else 0.62,
            f"《{source_name}》同时出现《{target_name}》的作者、年份和标题关键词。",
        )
    return None


def _fallback() -> dict[str, Any]:
    return {"relations": [], "is_mock": True}


def generate_paper_relations(
    papers: list[dict], relation_types: list[str]
) -> dict:
    """Generate stable, explainable relations from only the supplied papers."""
    normalized_papers = _normalize_papers(papers)
    if not normalized_papers or not isinstance(relation_types, list):
        return _fallback()
    requested = {
        item.strip()
        for item in relation_types
        if isinstance(item, str) and item.strip() in ALLOWED_RELATION_TYPES
    }
    if not requested:
        return _fallback()

    try:
        relations: list[dict[str, Any]] = []
        if "citation" in requested:
            relations.extend(
                relation
                for source, target in permutations(normalized_papers, 2)
                if (relation := _citation_relation(source, target)) is not None
            )
        for first, second in combinations(normalized_papers, 2):
            if "topic_similarity" in requested:
                relation = _topic_relation(first, second)
                if relation is not None:
                    relations.append(relation)
            if "method_similarity" in requested:
                relation = _method_relation(first, second)
                if relation is not None:
                    relations.append(relation)

        unique = {
            (relation["source"], relation["target"], relation["relation_type"]): relation
            for relation in relations
        }
        ordered = sorted(
            unique.values(),
            key=lambda item: (
                RELATION_ORDER[item["relation_type"]], item["source"], item["target"]
            ),
        )
        return {"relations": ordered, "is_mock": not bool(ordered)}
    except Exception as exc:
        logger.warning(
            "文献关系生成使用 fallback（reason=%s, papers=%d, relation_types=%d）",
            type(exc).__name__, len(normalized_papers), len(requested),
        )
        return _fallback()
