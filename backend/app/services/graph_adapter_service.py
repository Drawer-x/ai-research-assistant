"""Compatibility adapter for optional Sprint 3 relation generators."""

import importlib
import logging
from typing import Any

logger = logging.getLogger(__name__)
ALLOWED_TYPES = {"citation", "topic_similarity", "method_similarity"}


def _fallback(_papers: list[dict], _relation_types: list[str]) -> dict:
    return {"relations": [], "is_mock": True}


def _normalize(result: Any, papers: list[dict], relation_types: list[str]) -> dict | None:
    if not isinstance(result, dict) or not isinstance(result.get("relations"), list):
        return None
    valid_ids = {paper["paper_id"] for paper in papers}
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[int, int, str]] = set()
    for item in result["relations"]:
        if not isinstance(item, dict):
            continue
        source = item.get("source", item.get("source_paper_id"))
        target = item.get("target", item.get("target_paper_id"))
        relation_type = item.get("relation_type")
        if (
            source not in valid_ids
            or target not in valid_ids
            or source == target
            or relation_type not in ALLOWED_TYPES
            or relation_type not in relation_types
        ):
            continue
        if relation_type != "citation":
            source, target = sorted((source, target))
        key = (source, target, relation_type)
        if key in seen:
            continue
        seen.add(key)
        try:
            weight = float(item.get("weight", item.get("score", item.get("confidence", 0.5))))
        except (TypeError, ValueError):
            weight = 0.5
        normalized.append(
            {
                "source": source,
                "target": target,
                "relation_type": relation_type,
                "weight": min(1.0, max(0.0, weight)),
                "description": str(
                    item.get("description", item.get("relation_reason", "")) or ""
                ).strip(),
                "is_mock": item.get("is_mock") is True,
            }
        )
    is_mock = result.get("is_mock") is not False or not normalized
    if any(item["is_mock"] for item in normalized):
        is_mock = True
    return {"relations": normalized, "is_mock": is_mock}


def safe_generate_paper_relations(papers: list[dict], relation_types: list[str]) -> dict:
    """Call an available generator and normalize it to the HTTP-layer contract."""
    fallback = _fallback(papers, relation_types)
    # graph_service is checked for old deployments and test doubles. In normal
    # Sprint 3 deployments it has no generator entry, so the new pure service runs.
    candidates = (
        (
            "app.services.graph_service",
            ("generate_paper_relations", "build_paper_relations", "generate_literature_graph"),
        ),
        (
            "app.services.graph_generation_service",
            ("generate_paper_relations", "build_paper_relations", "generate_literature_graph"),
        ),
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
                logger.warning(
                    "关系生成使用 fallback（service=%s, reason=%s）",
                    name,
                    type(exc).__name__,
                )
                return fallback
    return fallback
