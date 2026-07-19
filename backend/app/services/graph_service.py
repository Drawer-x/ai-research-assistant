"""Build a useful paper graph from saved and lightweight inferred relations."""

import json
import re
from itertools import combinations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.paper import Paper
from app.models.relation import PaperRelation


RELATION_LABELS = {
    "similar_topic": "主题相似",
    "citation": "引用",
    "extends": "方法扩展",
    "method_similarity": "方法相似",
}
_STOP_WORDS = {
    "the", "and", "for", "with", "from", "this", "that", "using", "based",
    "paper", "study", "method", "research", "一种", "基于", "研究", "方法", "论文",
}
MAX_INFERENCE_PAPERS = 200
MAX_INFERRED_EDGES = 100


def _text_tokens(text: str) -> set[str]:
    text = text.lower()
    english = re.findall(r"[a-z0-9][a-z0-9+.-]{2,}", text)
    chinese: set[str] = set()
    for phrase in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        for width in range(2, min(4, len(phrase)) + 1):
            chinese.update(phrase[index:index + width] for index in range(len(phrase) - width + 1))
    return {token for token in (*english, *chinese) if token not in _STOP_WORDS}


def _weighted_tokens(paper: Paper) -> dict[str, float]:
    """Prioritize title, abstract and tags over a bounded body preview."""
    fields = (
        (paper.title, 4.0),
        (paper.abstract or "", 2.5),
        (" ".join(tag.name for tag in paper.tags), 3.0),
        ((paper.full_text or "")[:2_000], 1.0),
    )
    weights: dict[str, float] = {}
    for text, weight in fields:
        for token in _text_tokens(text):
            weights[token] = max(weights.get(token, 0.0), weight)
    return weights


def _weighted_jaccard(source: dict[str, float], target: dict[str, float]) -> tuple[int, float]:
    common = source.keys() & target.keys()
    union = source.keys() | target.keys()
    if not union:
        return 0, 0.0
    numerator = sum(min(source[token], target[token]) for token in common)
    denominator = sum(max(source.get(token, 0.0), target.get(token, 0.0)) for token in union)
    return len(common), numerator / denominator if denominator else 0.0


def _inferred_edges(papers: list[Paper], occupied: set[frozenset[int]]) -> list[dict]:
    edges: list[dict] = []
    inference_papers = papers[:MAX_INFERENCE_PAPERS]
    token_map = {paper.id: _weighted_tokens(paper) for paper in inference_papers}
    for source, target in combinations(inference_papers, 2):
        if frozenset((source.id, target.id)) in occupied:
            continue
        source_tokens, target_tokens = token_map[source.id], token_map[target.id]
        common_count, confidence = _weighted_jaccard(source_tokens, target_tokens)
        source_title = source.title.strip().casefold()
        target_title = target.title.strip().casefold()
        same_title = bool(source_title) and source_title == target_title
        if not same_title and (common_count < 2 or confidence < 0.08):
            continue
        if same_title:
            confidence = 1.0
        edges.append({
            "source": source.id,
            "target": target.id,
            "relation_type": "similar_topic",
            "label": RELATION_LABELS["similar_topic"],
            "relation_reason": "标题相同" if same_title else "根据标题、摘要、标签和正文关键词自动推断",
            "confidence": round(confidence, 3),
            "inferred": True,
        })
        if len(edges) >= MAX_INFERRED_EDGES:
            break
    return edges


def build_paper_graph(db: Session, user_id: int) -> dict:
    papers = list(db.scalars(
        select(Paper)
        .where(Paper.user_id == user_id)
        .options(selectinload(Paper.tags))
        .order_by(Paper.created_at.desc(), Paper.id.desc())
    ).all())
    paper_ids = [paper.id for paper in papers]
    relations: list[PaperRelation] = []
    if paper_ids:
        relations = list(db.scalars(
            select(PaperRelation)
            .where(
                PaperRelation.source_paper_id.in_(paper_ids),
                PaperRelation.target_paper_id.in_(paper_ids),
            )
            .order_by(PaperRelation.id)
        ).all())

    edges: list[dict] = []
    seen_relations: set[tuple[int, int, str]] = set()
    for relation in relations:
        relation_key = (relation.source_paper_id, relation.target_paper_id, relation.relation_type)
        if relation_key in seen_relations:
            continue
        seen_relations.add(relation_key)
        description, is_mock = relation.relation_reason, False
        try:
            metadata = json.loads(relation.relation_reason or "")
            if isinstance(metadata, dict):
                description = metadata.get("description")
                is_mock = bool(metadata.get("is_mock"))
        except (TypeError, json.JSONDecodeError):
            pass
        edges.append({
            "id": relation.id,
            "source": relation.source_paper_id,
            "target": relation.target_paper_id,
            "relation_type": relation.relation_type,
            "label": RELATION_LABELS.get(relation.relation_type, relation.relation_type),
            "relation_reason": description,
            "description": description,
            "confidence": relation.confidence,
            "weight": relation.confidence,
            "is_mock": is_mock,
            "inferred": False,
        })
    occupied = {frozenset((edge["source"], edge["target"])) for edge in edges}
    edges.extend(_inferred_edges(papers, occupied))

    return {
        "nodes": [
            {"id": paper.id, "paper_id": paper.id, "name": paper.title, "title": paper.title,
             "authors": paper.authors, "year": paper.year, "venue": paper.venue,
             "read_status": paper.read_status, "category": "paper"}
            for paper in papers
        ],
        "edges": edges,
    }
