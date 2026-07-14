"""Build a useful paper graph from saved and lightweight inferred relations."""

import re
from itertools import combinations

from sqlalchemy import select
from sqlalchemy.orm import Session

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


def _tokens(paper: Paper) -> set[str]:
    # Older uploads may have no extracted abstract, so use a bounded body
    # preview as a fallback without making graph construction scan full PDFs.
    text = f"{paper.title} {paper.abstract or ''} {(paper.full_text or '')[:2_000]}".lower()
    english = re.findall(r"[a-z0-9][a-z0-9+.-]{2,}", text)
    chinese = re.findall(r"[\u4e00-\u9fff]", text)
    return {token for token in (*english, *chinese) if token not in _STOP_WORDS}


def _inferred_edges(papers: list[Paper], occupied: set[frozenset[int]]) -> list[dict]:
    edges: list[dict] = []
    token_map = {paper.id: _tokens(paper) for paper in papers}
    for source, target in combinations(papers, 2):
        if frozenset((source.id, target.id)) in occupied:
            continue
        source_tokens, target_tokens = token_map[source.id], token_map[target.id]
        common = source_tokens & target_tokens
        union = source_tokens | target_tokens
        confidence = len(common) / len(union) if union else 0.0
        same_title = source.title.strip().casefold() == target.title.strip().casefold()
        if not same_title and (len(common) < 2 or confidence < 0.08):
            continue
        if same_title:
            confidence = 1.0
        edges.append({
            "source": source.id,
            "target": target.id,
            "relation_type": "similar_topic",
            "label": RELATION_LABELS["similar_topic"],
            "relation_reason": "标题相同" if same_title else "根据标题、摘要和正文关键词自动推断",
            "confidence": round(confidence, 3),
            "inferred": True,
        })
        if len(edges) >= 100:
            break
    return edges


def build_paper_graph(db: Session, user_id: int) -> dict:
    papers = list(db.scalars(
        select(Paper).where(Paper.user_id == user_id).order_by(Paper.created_at.desc(), Paper.id.desc())
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

    edges = [
        {
            "source": relation.source_paper_id,
            "target": relation.target_paper_id,
            "relation_type": relation.relation_type,
            "label": RELATION_LABELS.get(relation.relation_type, relation.relation_type),
            "relation_reason": relation.relation_reason,
            "confidence": relation.confidence,
            "inferred": False,
        }
        for relation in relations
    ]
    occupied = {frozenset((edge["source"], edge["target"])) for edge in edges}
    edges.extend(_inferred_edges(papers, occupied))

    return {
        "nodes": [
            {"id": paper.id, "name": paper.title, "year": paper.year, "category": "paper"}
            for paper in papers
        ],
        "edges": edges,
    }
