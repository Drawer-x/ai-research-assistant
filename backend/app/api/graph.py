from fastapi import APIRouter, Depends
import json

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.paper import Paper
from app.models.relation import PaperRelation
from app.schemas.graph import GraphGenerateRequest
from app.services.graph_adapter_service import safe_generate_paper_relations
from app.services.graph_service import build_paper_graph

router = APIRouter(prefix="/graph", tags=["文献关系图"])


@router.get("/papers")
def paper_graph(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(build_paper_graph(db, current_user.id))


@router.get("/relations")
def relations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(build_paper_graph(db, current_user.id)["edges"])


@router.post("/generate")
def generate_graph(payload: GraphGenerateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    statement = select(Paper).where(Paper.user_id == current_user.id)
    if payload.paper_ids:
        statement = statement.where(Paper.id.in_(payload.paper_ids))
    papers = list(db.scalars(statement.order_by(Paper.id)).all())
    if payload.paper_ids and len(papers) != len(payload.paper_ids):
        return error_response("部分文献不存在或无权访问", 404)
    if len(papers) < 2:
        return error_response("至少需要两篇文献", 400)
    ids = [paper.id for paper in papers]
    if payload.force_regenerate:
        db.execute(delete(PaperRelation).where(
            PaperRelation.source_paper_id.in_(ids), PaperRelation.target_paper_id.in_(ids),
            PaperRelation.relation_type.in_(payload.relation_types),
        ))
    paper_data = [{"paper_id": paper.id, "title": paper.title, "authors": paper.authors,
                   "year": paper.year, "venue": paper.venue, "abstract": paper.abstract,
                   "full_text": (paper.full_text or "")[:4000]} for paper in papers]
    result = safe_generate_paper_relations(paper_data, payload.relation_types)
    existing = set(db.execute(select(
        PaperRelation.source_paper_id, PaperRelation.target_paper_id, PaperRelation.relation_type
    ).where(PaperRelation.source_paper_id.in_(ids), PaperRelation.target_paper_id.in_(ids))).all())
    created = 0
    for relation in result["relations"]:
        key = (relation["source"], relation["target"], relation["relation_type"])
        if key in existing:
            continue
        db.add(PaperRelation(
            source_paper_id=relation["source"], target_paper_id=relation["target"],
            relation_type=relation["relation_type"], confidence=relation["weight"],
            relation_reason=json.dumps({"description": relation["description"], "is_mock": relation["is_mock"]}, ensure_ascii=False),
        ))
        existing.add(key); created += 1
    try:
        db.commit()
    except Exception:
        db.rollback()
        return error_response("关系保存失败", 500)
    graph = build_paper_graph(db, current_user.id)
    graph.update({"is_mock": result["is_mock"], "generated_count": created})
    return success_response(graph)
