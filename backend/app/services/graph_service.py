# graph_service.py

from sqlalchemy import or_, select

from app.models.paper import Paper
from app.models.relation import PaperRelation


RELATION_LABELS = {"similar_topic": "主题相似", "citation": "引用", "extends": "方法扩展"}


def build_paper_graph(db, user_id: int) -> dict:
    papers = db.scalars(select(Paper).where(Paper.user_id == user_id)).all()
    paper_ids = {paper.id for paper in papers}
    relations = []
    if paper_ids:
        relations = db.scalars(select(PaperRelation).where(
            PaperRelation.source_paper_id.in_(paper_ids), PaperRelation.target_paper_id.in_(paper_ids)
        )).all()
    return {
        "nodes": [{"id": p.id, "name": p.title, "year": p.year, "category": "paper"} for p in papers],
        "edges": [{"source": r.source_paper_id, "target": r.target_paper_id, "relation_type": r.relation_type,
                   "label": RELATION_LABELS.get(r.relation_type, r.relation_type)} for r in relations],
    }
