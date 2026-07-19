"""Compatibility adapter for optional Sprint 3 relation generators."""

import importlib
import logging
from itertools import combinations
from typing import Any

logger = logging.getLogger(__name__)
ALLOWED_TYPES = {"citation", "topic_similarity", "method_similarity"}


def _fallback(papers: list[dict], relation_types: list[str]) -> dict:
    relation_type = "topic_similarity" if "topic_similarity" in relation_types else relation_types[0]
    relations = [
        {
            "source": first["paper_id"], "target": second["paper_id"],
            "relation_type": relation_type, "weight": 0.5,
            "description": "用于联调的确定性 fallback 关系，不代表精确算法结果。", "is_mock": True,
        }
        for first, second in combinations(papers, 2)
    ]
    return {"relations": relations, "is_mock": True}


def _normalize(result: Any, papers: list[dict], relation_types: list[str]) -> dict | None:
    if not isinstance(result, dict) or not isinstance(result.get("relations"), list):
        return None
    valid_ids = {paper["paper_id"] for paper in papers}
    normalized, seen = [], set()
    for item in result["relations"]:
        if not isinstance(item, dict):
            continue
        source, target = item.get("source", item.get("source_paper_id")), item.get("target", item.get("target_paper_id"))
        relation_type = item.get("relation_type")
        if source not in valid_ids or target not in valid_ids or source == target or relation_type not in ALLOWED_TYPES or relation_type not in relation_types:
            continue
        source, target = sorted((source, target))
        key = (source, target, relation_type)
        if key in seen:
            continue
        seen.add(key)
        try:
            weight = float(item.get("weight", item.get("score", item.get("confidence", 0.5))))
        except (TypeError, ValueError):
            weight = 0.5
        normalized.append({
            "source": source, "target": target, "relation_type": relation_type,
            "weight": min(1.0, max(0.0, weight)),
            "description": str(item.get("description", item.get("relation_reason", "")) or "").strip(),
            "is_mock": item.get("is_mock") is True,
        })
    return {"relations": normalized, "is_mock": bool(result.get("is_mock", False))}


def safe_generate_paper_relations(papers: list[dict], relation_types: list[str]) -> dict:
    fallback = _fallback(papers, relation_types)
    candidates = (
        ("app.services.graph_generation_service", ("generate_paper_relations", "build_paper_relations", "generate_literature_graph")),
        ("app.services.graph_service", ("generate_paper_relations", "build_paper_relations", "generate_literature_graph")),
    )
    for module_name, names in candidates:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        for name in names:
            function = getattr(module, name, None)
            if not callable(function):
                continue
            try:
                normalized = _normalize(function(papers, relation_types), papers, relation_types)
                return normalized if normalized is not None else fallback
            except Exception as exc:
                logger.warning("关系生成使用 fallback（service=%s, reason=%s）", name, type(exc).__name__)
                return fallback
    return fallback
