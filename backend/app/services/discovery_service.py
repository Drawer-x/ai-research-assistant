import json
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.paper import Paper
from app.models.paper_external_source import PaperExternalSource
from app.services.semantic_scholar_client import SemanticScholarClient, normalize_doi, normalize_title

def _mark_imported(db,user_id,papers):
    ids=[p["external_id"] for p in papers]
    sources=db.scalars(select(PaperExternalSource).where(PaperExternalSource.user_id==user_id,PaperExternalSource.provider=="semantic_scholar",PaperExternalSource.external_id.in_(ids))).all() if ids else []
    found={s.external_id:s.paper_id for s in sources}
    for p in papers: p["is_imported"]=p["external_id"] in found; p["local_paper_id"]=found.get(p["external_id"])
    return papers
def search_external_papers(db,user_id,**kwargs):
    result=SemanticScholarClient().search_papers(**kwargs); _mark_imported(db,user_id,result["items"]); return result
def get_external_paper(db,user_id,external_id):
    paper=SemanticScholarClient().get_paper(external_id); _mark_imported(db,user_id,[paper]); return paper
def resolve_local_paper_external_id(db,paper,user_id):
    source=db.scalar(select(PaperExternalSource).where(PaperExternalSource.paper_id==paper.id,PaperExternalSource.user_id==user_id))
    if source:return source.external_id
    return SemanticScholarClient().resolve_paper_id(paper.title)
def import_external_paper(db:Session,user_id:int,provider:str,external_id:str,paper_snapshot=None):
    if provider!="semantic_scholar": raise ValueError("unsupported provider")
    data=paper_snapshot or SemanticScholarClient().get_paper(external_id); external_id=data["external_id"] or external_id
    source=db.scalar(select(PaperExternalSource).where(PaperExternalSource.user_id==user_id,PaperExternalSource.provider==provider,PaperExternalSource.external_id==external_id))
    if source:return {"paper_id":source.paper_id,"already_imported":True,"paper":data}
    duplicate=None
    if data.get("doi"):
        duplicate=db.scalar(select(PaperExternalSource).where(PaperExternalSource.user_id==user_id,func.lower(PaperExternalSource.doi)==normalize_doi(data["doi"])))
    if not duplicate:
        candidates=db.scalars(select(Paper).where(Paper.user_id==user_id,Paper.year==data.get("year"))).all()
        match=next((p for p in candidates if normalize_title(p.title).casefold()==normalize_title(data["title"]).casefold()),None)
        if match:
            duplicate=PaperExternalSource(user_id=user_id,paper_id=match.id,provider=provider,external_id=external_id)
            _fill_source(duplicate,data); db.add(duplicate); db.commit()
    if duplicate:return {"paper_id":duplicate.paper_id,"already_imported":True,"paper":data}
    paper=Paper(user_id=user_id,title=data["title"] or "Untitled",authors=", ".join(a["name"] for a in data["authors"]),year=data["year"],venue=data["venue"],abstract=data["abstract"],pdf_path=f"external://semantic-scholar/{external_id}",full_text=None,parse_status="external")
    db.add(paper); db.flush(); source=PaperExternalSource(user_id=user_id,paper_id=paper.id,provider=provider,external_id=external_id); _fill_source(source,data); db.add(source); db.commit(); db.refresh(paper)
    data["is_imported"]=True; data["local_paper_id"]=paper.id
    return {"paper_id":paper.id,"already_imported":False,"paper":data}
def _fill_source(source,data):
    source.doi=data.get("doi"); source.arxiv_id=data.get("arxiv_id"); source.external_url=data.get("external_url"); source.pdf_url=data.get("pdf_url"); source.abstract=data.get("abstract"); source.citation_count=data.get("citation_count",0); source.reference_count=data.get("reference_count",0); source.fields_of_study_json=json.dumps(data.get("fields_of_study",[])); source.metadata_json=json.dumps(data,ensure_ascii=False)
