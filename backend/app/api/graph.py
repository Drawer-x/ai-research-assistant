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
from app.schemas.graph import GraphExpandRequest, GraphGenerateRequest
from app.models.paper_recommendation import PaperRecommendation
from app.services.discovery_service import resolve_local_paper_external_id
from app.services.crossref_client import CrossrefClient
from app.services.graph_adapter_service import safe_generate_paper_relations
from app.services.graph_service import build_paper_graph

router = APIRouter(prefix="/graph", tags=["文献关系图"])


@router.get("/relation-types")
def relation_types(current_user: User = Depends(get_current_user)):
    return success_response(["citation", "topic_similarity", "method_similarity", "same_author", "recommended_from"])

def _external_node(p, kind="external", record_id=None):
    return {"id":f"recommendation:{record_id}" if record_id else f"crossref:{p.get('external_id')}","node_type":kind,"paper_id":None,"external_id":p.get("external_id"),"title":p.get("title"),"year":p.get("year"),"source":"crossref","imported":False,"category":1}

@router.get("/enhanced")
def enhanced(paper_ids: list[int] = None, relation_types: list[str] = None, min_weight: float = 0, include_external: bool = True, max_nodes: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not 0 <= min_weight <= 1 or not 1 <= max_nodes <= 100: return error_response("invalid graph limits", 422)
    q=select(Paper).where(Paper.user_id==current_user.id)
    if paper_ids:q=q.where(Paper.id.in_(paper_ids))
    papers=list(db.scalars(q.order_by(Paper.id)).all())
    if paper_ids and len(papers)!=len(set(paper_ids)):return error_response("paper not found",404)
    ids=[p.id for p in papers];nodes=[{"id":f"local:{p.id}","node_type":"local","paper_id":p.id,"external_id":None,"title":p.title,"year":p.year,"source":"local","imported":True,"category":0} for p in papers];edges=[]
    for r in db.scalars(select(PaperRelation).where(PaperRelation.source_paper_id.in_(ids),PaperRelation.target_paper_id.in_(ids))).all():
        w=float(r.confidence or 0)
        if w>=min_weight and (not relation_types or r.relation_type in relation_types):edges.append({"source":f"local:{r.source_paper_id}","target":f"local:{r.target_paper_id}","relation_type":r.relation_type,"weight":w,"description":r.relation_reason or "Persisted relation","directed":True,"is_fallback":True})
    if include_external:
        for r in db.scalars(select(PaperRecommendation).where(PaperRecommendation.user_id==current_user.id).order_by(PaperRecommendation.updated_at.desc())).all():
            snap=json.loads(r.paper_snapshot_json);seeds=json.loads(r.seed_paper_ids_json)
            if not any(s in ids for s in seeds):continue
            nodes.append(_external_node(snap,"recommended",r.id))
            for seed in seeds:
                if seed in ids and r.score>=min_weight:edges.append({"source":f"local:{seed}","target":f"recommendation:{r.id}","relation_type":"recommended_from","weight":r.score,"description":"Persisted recommendation","directed":True,"is_fallback":r.is_fallback})
    unique={n["id"]:n for n in nodes};truncated=len(unique)>max_nodes;allowed=set(list(unique)[:max_nodes]);nodes=[unique[x] for x in allowed];edges=[e for e in edges if e["source"] in allowed and e["target"] in allowed and e["source"]!=e["target"]]
    return success_response({"nodes":nodes,"edges":edges,"meta":{"total_nodes":len(nodes),"total_edges":len(edges),"truncated":truncated,"is_fallback":any(e["is_fallback"] for e in edges)}})

@router.post("/expand")
def expand(payload:GraphExpandRequest,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if payload.expand_type not in {"recommendation","references","citations"}:return error_response("invalid expand_type",422)
    if not payload.node_id.startswith("local:"):return error_response("only owned local nodes may be expanded",422)
    try:pid=int(payload.node_id.split(":",1)[1])
    except ValueError:return error_response("invalid node_id",422)
    paper=db.scalar(select(Paper).where(Paper.id==pid,Paper.user_id==current_user.id))
    if not paper:return error_response("paper not found",404)
    eid=resolve_local_paper_external_id(db,paper,current_user.id)
    if not eid:return error_response("paper cannot be resolved",422)
    client=CrossrefClient(); citation_scope=None
    if payload.expand_type=="recommendation":
        recommendation_fallback=False
        seed=client.get_work(eid);query=" ".join([seed.get("title") or ""]+[a.get("name","") for a in seed.get("authors",[])[:2]])[:180];items=client.search_works(query,page_size=min(payload.limit*2,50))["items"];items=[p for p in items if p.get("external_id")!=eid][:payload.limit]
    elif payload.expand_type=="references": items=client.get_references(eid,payload.limit)
    else:
        # Crossref has no citing-papers endpoint. Never substitute relevance search.
        items=[];citation_scope="known_records_only"
    nodes=[_external_node(p) for p in items];rtype="recommended_from" if payload.expand_type=="recommendation" else "citation";description="Academic Graph search fallback" if payload.expand_type=="recommendation" and recommendation_fallback else payload.expand_type;edges=[{"source":payload.node_id if payload.expand_type!="citations" else n["id"],"target":n["id"] if payload.expand_type!="citations" else payload.node_id,"relation_type":rtype,"weight":1.0,"description":description,"directed":True,"is_fallback":recommendation_fallback if payload.expand_type=="recommendation" else False} for n in nodes]
    return success_response({"nodes":nodes,"edges":edges,"meta":{"total_nodes":len(nodes),"total_edges":len(edges),"truncated":False,"is_fallback":False,"citation_scope":citation_scope}})

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
