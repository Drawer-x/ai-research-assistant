import json
from sqlalchemy import select
from app.models.paper import Paper
from app.models.paper_external_source import PaperExternalSource
from app.models.paper_recommendation import PaperRecommendation
from app.services.discovery_service import import_external_paper,resolve_local_paper_external_id
from app.services.recommendation_adapter_service import recommend_by_paper,recommend_by_topic,recommend_for_library
from app.services.semantic_scholar_client import SemanticScholarClient,SemanticScholarError,normalize_doi,normalize_title
def serialize(r): return {"id":r.id,"mode":r.recommendation_mode,"paper":json.loads(r.paper_snapshot_json),"score":r.score,"reasons":json.loads(r.reasons_json),"seed_paper_ids":json.loads(r.seed_paper_ids_json),"status":r.status,"is_fallback":r.is_fallback,"created_at":r.created_at,"updated_at":r.updated_at}
def _persist(db,user_id,mode,items,seeds):
    out=[]
    for item in items:
        p=item["paper"]; eid=p.get("external_id")
        if not eid: continue
        r=db.scalar(select(PaperRecommendation).where(PaperRecommendation.user_id==user_id,PaperRecommendation.provider=="semantic_scholar",PaperRecommendation.external_id==eid))
        if r and r.status=="not_interested": continue
        if not r:r=PaperRecommendation(user_id=user_id,provider="semantic_scholar",external_id=eid,recommendation_mode=mode,paper_snapshot_json="{}")
        r.seed_paper_ids_json=json.dumps(seeds);r.recommendation_mode=mode;r.paper_snapshot_json=json.dumps(p,ensure_ascii=False);r.score=max(0,min(1,float(item.get("score",0))));r.reasons_json=json.dumps(item.get("reasons",[]),ensure_ascii=False);r.is_fallback=bool(item.get("is_fallback"));db.add(r);out.append(r)
    db.commit()
    for r in out:db.refresh(r)
    return [serialize(r) for r in out]
def _filter(db,user_id,candidates,seed_ids=()):
    local=db.scalars(select(Paper).where(Paper.user_id==user_id)).all(); sources=db.scalars(select(PaperExternalSource).where(PaperExternalSource.user_id==user_id)).all()
    ext={s.external_id for s in sources}; ext.update(db.scalars(select(PaperRecommendation.external_id).where(PaperRecommendation.user_id==user_id,PaperRecommendation.status=="not_interested")).all()); dois={normalize_doi(s.doi) for s in sources if s.doi}; titles={normalize_title(p.title).casefold() for p in local}
    return [p for p in candidates if p.get("external_id") not in ext and normalize_doi(p.get("doi")) not in dois and normalize_title(p.get("title")).casefold() not in titles and p.get("external_id") not in seed_ids]
def _search_query(papers):
    words=[]
    for p in papers[:5]:
        fields=p.get("fields_of_study",[]) if isinstance(p,dict) else []
        title=p.get("title","") if isinstance(p,dict) else p.title
        words.extend(str(x) for x in fields[:2]);words.extend(w.strip(".,:;()[]").lower() for w in normalize_title(title).split() if len(w)>3)
    unique=[]
    for word in words:
        if word and word.casefold() not in {x.casefold() for x in unique}:unique.append(word)
    return " ".join(unique[:8])[:180] or "research"
def _academic_candidates(client,papers,limit):return client.search_papers(_search_query(papers),page_size=min(100,max(20,limit*2)))["items"]
def by_paper(db,user_id,paper_id,limit):
    p=db.scalar(select(Paper).where(Paper.id==paper_id,Paper.user_id==user_id));
    if not p: raise LookupError("paper not found")
    eid=resolve_local_paper_external_id(db,p,user_id)
    if not eid: raise ValueError("paper cannot be resolved on Semantic Scholar")
    client=SemanticScholarClient();seed=client.get_paper(eid)
    try:candidates=client.get_recommendations_for_paper(eid,max(limit*2,20))
    except SemanticScholarError:candidates=_academic_candidates(client,[seed],limit)
    c=_filter(db,user_id,candidates,[eid]);result=recommend_by_paper({**seed,"paper_id":p.id},c,limit);return _persist(db,user_id,"by_paper",result["items"],[paper_id])
def for_library(db,user_id,paper_ids,limit):
    papers=db.scalars(select(Paper).where(Paper.user_id==user_id,Paper.id.in_(paper_ids))).all()
    if len(papers)!=len(set(paper_ids)): raise LookupError("paper not found")
    pairs=[(p,resolve_local_paper_external_id(db,p,user_id)) for p in papers]; pairs=[x for x in pairs if x[1]]
    if not pairs: raise ValueError("no resolvable seed papers")
    negatives=list(db.scalars(select(PaperRecommendation.external_id).where(PaperRecommendation.user_id==user_id,PaperRecommendation.status=="not_interested")))
    client=SemanticScholarClient();seed_data=[client.get_paper(eid) for _,eid in pairs]
    try:candidates=client.get_recommendations_for_seeds([x[1] for x in pairs],negatives,max(limit*2,20))
    except SemanticScholarError:candidates=_academic_candidates(client,seed_data,limit)
    c=_filter(db,user_id,candidates,[x[1] for x in pairs]);result=recommend_for_library([{**d,"paper_id":p.id} for (p,_),d in zip(pairs,seed_data)],c,negatives,limit);return _persist(db,user_id,"for_library",result["items"],paper_ids)
def by_topic(db,user_id,topic,year_from,year_to,limit):
    c=_filter(db,user_id,SemanticScholarClient().search_papers(topic,year_from,year_to,page_size=50)["items"]);result=recommend_by_topic(topic,c,year_from,year_to,limit);return _persist(db,user_id,"by_topic",result["items"],[])
def import_recommendation(db,user_id,r):
    result=import_external_paper(db,user_id,r.provider,r.external_id,json.loads(r.paper_snapshot_json));r.status="imported";db.commit();return result
