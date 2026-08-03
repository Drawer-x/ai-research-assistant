"""Deterministic enhanced literature relations for Sprint 4 (member B).

Pure functions only: no database, JWT, or HTTP. Never invents papers or edges
without evidence from the supplied inputs.
"""

from __future__ import annotations

import math
import re
from itertools import combinations, permutations
from typing import Any

ALLOWED_RELATION_TYPES = {
    "citation",
    "topic_similarity",
    "method_similarity",
    "same_author",
    "recommended_from",
}
RELATION_ORDER = {
    "citation": 0,
    "topic_similarity": 1,
    "method_similarity": 2,
    "same_author": 3,
    "recommended_from": 4,
}

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


def _safe_text(value: Any, limit: int = 4_000) -> str:
    return re.sub(r"\s+", " ", value).strip()[:limit] if isinstance(value, str) else ""


def _normalize_search_text(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", value.casefold()).strip()


def _clamp01(value: float) -> float:
    if not math.isfinite(value):
        return 0.0
    return max(0.0, min(1.0, float(value)))


def _text_tokens(text: str) -> set[str]:
    normalized = _normalize_search_text(text)
    english = re.findall(r"[a-z0-9][a-z0-9+#.-]{1,}", text.casefold())
    chinese: set[str] = set()
    for phrase in re.findall(r"[\u4e00-\u9fff]{2,}", normalized):
        for width in range(2, min(4, len(phrase)) + 1):
            chinese.update(phrase[i:i + width] for i in range(len(phrase) - width + 1))
    return {
        token for token in (*english, *chinese)
        if token not in _STOP_WORDS and len(token) >= 2
    }


def _author_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        names: list[str] = []
        for item in value:
            if isinstance(item, dict):
                name = _safe_text(item.get("name"), 200)
                if name:
                    names.append(name)
            elif isinstance(item, str) and item.strip():
                names.append(item.strip())
        return ", ".join(names)
    return ""


def _author_markers(authors: str) -> set[str]:
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
    return markers


def _node_id_local(paper_id: int) -> str:
    return f"local:{paper_id}"


def _node_id_external(external_id: str) -> str:
    return f"s2:{external_id}"


def _node_id_recommendation(record_id: int) -> str:
    return f"recommendation:{record_id}"


def _normalize_local_papers(papers: Any) -> list[dict[str, Any]]:
    if not isinstance(papers, list):
        return []
    normalized: list[dict[str, Any]] = []
    seen: set[int] = set()
    for paper in papers:
        if not isinstance(paper, dict):
            continue
        paper_id = paper.get("paper_id")
        if not isinstance(paper_id, int) or isinstance(paper_id, bool) or paper_id <= 0:
            continue
        if paper_id in seen:
            continue
        seen.add(paper_id)
        authors = _author_text(paper.get("authors"))
        normalized.append(
            {
                "node_id": _node_id_local(paper_id),
                "paper_id": paper_id,
                "external_id": None,
                "title": _safe_text(paper.get("title"), 500),
                "authors": authors,
                "author_markers": _author_markers(authors),
                "year": paper.get("year") if isinstance(paper.get("year"), int) and not isinstance(paper.get("year"), bool) else None,
                "venue": _safe_text(paper.get("venue"), 300),
                "abstract": _safe_text(paper.get("abstract"), 3_000),
                "full_text": _safe_text(paper.get("full_text"), 12_000),
                "fields_of_study": [
                    str(item) for item in (paper.get("fields_of_study") or []) if isinstance(item, str)
                ],
            }
        )
    return sorted(normalized, key=lambda item: item["paper_id"])


def _normalize_external_papers(papers: Any) -> list[dict[str, Any]]:
    if not isinstance(papers, list):
        return []
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for paper in papers:
        if not isinstance(paper, dict):
            continue
        external_id = str(paper.get("external_id") or "").strip()
        if not external_id or external_id in seen:
            continue
        seen.add(external_id)
        authors = _author_text(paper.get("authors"))
        normalized.append(
            {
                "node_id": _node_id_external(external_id),
                "paper_id": None,
                "external_id": external_id,
                "title": _safe_text(paper.get("title"), 500),
                "authors": authors,
                "author_markers": _author_markers(authors),
                "year": paper.get("year") if isinstance(paper.get("year"), int) and not isinstance(paper.get("year"), bool) else None,
                "venue": _safe_text(paper.get("venue"), 300),
                "abstract": _safe_text(paper.get("abstract"), 3_000),
                "full_text": _safe_text(paper.get("full_text"), 12_000),
                "fields_of_study": [
                    str(item) for item in (paper.get("fields_of_study") or []) if isinstance(item, str)
                ],
            }
        )
    return sorted(normalized, key=lambda item: item["external_id"])


def _weighted_tokens(paper: dict[str, Any]) -> dict[str, float]:
    field_text = " ".join(paper.get("fields_of_study") or [])
    parts = (
        (paper["title"], 4.0),
        (paper["abstract"], 2.5),
        (field_text, 3.0),
        (paper["authors"], 0.4),
        (paper["venue"], 0.4),
        (paper["full_text"][:4_000], 1.0),
    )
    weights: dict[str, float] = {}
    for text, weight in parts:
        for token in _text_tokens(text):
            weights[token] = max(weights.get(token, 0.0), weight)
    return weights


def _weighted_jaccard(left: dict[str, float], right: dict[str, float]) -> tuple[set[str], float]:
    union = left.keys() | right.keys()
    if not union:
        return set(), 0.0
    common = left.keys() & right.keys()
    numerator = sum(min(left[token], right[token]) for token in common)
    denominator = sum(max(left.get(token, 0.0), right.get(token, 0.0)) for token in union)
    return common, numerator / denominator if denominator else 0.0


def _display_keywords(common: set[str], left: dict[str, float], right: dict[str, float], limit: int = 3) -> list[str]:
    ranked = sorted(common, key=lambda token: (-min(left[token], right[token]), -len(token), token))
    selected: list[str] = []
    for token in ranked:
        if any(token in existing or existing in token for existing in selected):
            continue
        selected.append(token)
        if len(selected) >= limit:
            break
    return selected


def _relation(
    source: str,
    target: str,
    relation_type: str,
    weight: float,
    description: str,
    *,
    directed: bool,
) -> dict[str, Any] | None:
    if not source or not target or source == target:
        return None
    weight_n = round(_clamp01(weight), 6)
    return {
        "source": source,
        "target": target,
        "relation_type": relation_type,
        "weight": weight_n,
        "description": description,
        "directed": bool(directed),
        "is_fallback": False,
    }


def _ordered_pair(first: dict[str, Any], second: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if first["node_id"] <= second["node_id"]:
        return first, second
    return second, first


def _topic_relation(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any] | None:
    left = _weighted_tokens(first)
    right = _weighted_tokens(second)
    common, score = _weighted_jaccard(left, right)
    same_title = bool(first["title"]) and (
        _normalize_search_text(first["title"]) == _normalize_search_text(second["title"])
    )
    if not same_title and (len(common) < 2 or score < 0.08):
        return None
    keywords = _display_keywords(common, left, right)
    if same_title:
        description = "两篇论文标题相同，主题高度一致。"
        weight = 1.0
    else:
        description = f"两篇论文的真实文本共同涉及{'、'.join(keywords)}。"
        weight = min(0.95, max(0.1, score))
    source, target = _ordered_pair(first, second)
    return _relation(
        source["node_id"], target["node_id"], "topic_similarity", weight, description, directed=False
    )


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


def _method_relation(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any] | None:
    left_methods, right_methods = _method_set(first), _method_set(second)
    common = left_methods & right_methods
    if not common:
        return None
    union = left_methods | right_methods
    overlap = len(common) / len(union)
    weight = min(0.98, 0.55 + 0.4 * overlap + 0.02 * (len(common) - 1))
    source, target = _ordered_pair(first, second)
    return _relation(
        source["node_id"],
        target["node_id"],
        "method_similarity",
        weight,
        f"两篇论文共同采用{'、'.join(sorted(common))}方法。",
        directed=False,
    )


def _same_author_relation(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any] | None:
    common = first["author_markers"] & second["author_markers"]
    if not common:
        return None
    union = first["author_markers"] | second["author_markers"]
    weight = min(0.95, 0.55 + 0.4 * (len(common) / max(len(union), 1)))
    labels = "、".join(sorted(common)[:3])
    source, target = _ordered_pair(first, second)
    return _relation(
        source["node_id"],
        target["node_id"],
        "same_author",
        weight,
        f"两篇论文共享作者标记：{labels}。",
        directed=False,
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


def _citation_relation(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any] | None:
    target_title = target["title"]
    if not _title_is_specific(target_title) or not source["full_text"]:
        return None
    normalized_title = _normalize_search_text(target_title)
    normalized_body = _normalize_search_text(source["full_text"])
    references = _reference_section(source["full_text"])
    normalized_references = _normalize_search_text(references)
    source_name = source["title"] or source["node_id"]
    target_name = target_title or target["node_id"]

    if normalized_references and normalized_title in normalized_references:
        return _relation(
            source["node_id"],
            target["node_id"],
            "citation",
            0.96,
            f"《{source_name}》的参考文献区域出现了《{target_name}》的完整标题。",
            directed=True,
        )
    if normalized_title in normalized_body:
        return _relation(
            source["node_id"],
            target["node_id"],
            "citation",
            0.85,
            f"《{source_name}》正文出现了《{target_name}》的完整标题。",
            directed=True,
        )

    year = str(target["year"]) if target["year"] is not None else ""
    title_tokens = {
        token for token in _text_tokens(target_title)
        if len(token) >= 3 and token not in _STOP_WORDS
    }
    common_keywords = title_tokens & _text_tokens(source["full_text"])
    evidence_text = normalized_references or normalized_body
    has_author = any(marker in evidence_text for marker in target["author_markers"])
    if year and year in evidence_text and has_author and len(common_keywords) >= 2:
        return _relation(
            source["node_id"],
            target["node_id"],
            "citation",
            0.68 if normalized_references else 0.62,
            f"《{source_name}》同时出现《{target_name}》的作者、年份和标题关键词。",
            directed=True,
        )
    return None


def _recommended_relations(records: Any, local_ids: set[int], relation_types: set[str]) -> list[dict[str, Any]]:
    if "recommended_from" not in relation_types or not isinstance(records, list):
        return []
    relations: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        record_id = record.get("id")
        if not isinstance(record_id, int) or isinstance(record_id, bool) or record_id <= 0:
            continue
        seeds = record.get("seed_paper_ids") or []
        if not isinstance(seeds, list):
            continue
        score = record.get("score", 0)
        try:
            weight = _clamp01(float(score))
        except (TypeError, ValueError):
            weight = 0.0
        target = _node_id_recommendation(record_id)
        for seed in seeds:
            if not isinstance(seed, int) or isinstance(seed, bool) or seed not in local_ids:
                continue
            relation = _relation(
                _node_id_local(seed),
                target,
                "recommended_from",
                weight,
                "基于推荐记录生成的推荐关系。",
                directed=True,
            )
            if relation is not None:
                relations.append(relation)
    return relations


def generate_enhanced_relations(
    local_papers: list[dict],
    external_papers: list[dict],
    recommendation_records: list[dict],
    relation_types: list[str],
) -> dict:
    """Generate enhanced relations from supplied local/external papers and records."""
    if not isinstance(relation_types, list):
        return {"relations": []}
    requested = {
        item.strip()
        for item in relation_types
        if isinstance(item, str) and item.strip() in ALLOWED_RELATION_TYPES
    }
    if not requested:
        return {"relations": []}

    locals_n = _normalize_local_papers(local_papers)
    externals_n = _normalize_external_papers(external_papers)
    all_papers = [*locals_n, *externals_n]
    local_ids = {paper["paper_id"] for paper in locals_n}

    relations: list[dict[str, Any]] = []
    try:
        if "recommended_from" in requested:
            relations.extend(_recommended_relations(recommendation_records, local_ids, requested))

        pairwise_types = requested & {"topic_similarity", "method_similarity", "same_author"}
        if pairwise_types and len(all_papers) >= 2:
            for first, second in combinations(all_papers, 2):
                if "topic_similarity" in pairwise_types:
                    relation = _topic_relation(first, second)
                    if relation is not None:
                        relations.append(relation)
                if "method_similarity" in pairwise_types:
                    relation = _method_relation(first, second)
                    if relation is not None:
                        relations.append(relation)
                if "same_author" in pairwise_types:
                    relation = _same_author_relation(first, second)
                    if relation is not None:
                        relations.append(relation)

        if "citation" in requested and len(all_papers) >= 2:
            for source, target in permutations(all_papers, 2):
                relation = _citation_relation(source, target)
                if relation is not None:
                    relations.append(relation)

        unique = {
            (item["source"], item["target"], item["relation_type"]): item
            for item in relations
            if item["source"] != item["target"]
            and math.isfinite(item["weight"])
            and 0.0 <= item["weight"] <= 1.0
        }
        ordered = sorted(
            unique.values(),
            key=lambda item: (
                RELATION_ORDER[item["relation_type"]],
                item["source"],
                item["target"],
            ),
        )
        return {"relations": ordered}
    except Exception:
        return {"relations": []}
