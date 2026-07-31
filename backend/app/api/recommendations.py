from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.response import success_response
from app.core.security import get_current_user
from app.database import get_db
from app.models.paper_recommendation import PaperRecommendation
from app.models.user import User
from app.schemas.recommendations import *
from app.services import recommendation_orchestration_service as svc
router=APIRouter(prefix="/recommendations",tags=["Recommendations"])
@router.post("/by-paper")
def by_paper(p:ByPaperRequest,db:Session=Depends(get_db),u:User=Depends(get_current_user)): return success_response(svc.by_paper(db,u.id,p.paper_id,p.limit))
@router.post("/for-library")
def for_library(p:ForLibraryRequest,db:Session=Depends(get_db),u:User=Depends(get_current_user)): return success_response(svc.for_library(db,u.id,p.paper_ids,p.limit))
@router.post("/by-topic")
def by_topic(p:ByTopicRequest,db:Session=Depends(get_db),u:User=Depends(get_current_user)): return success_response(svc.by_topic(db,u.id,p.topic,p.year_from,p.year_to,p.limit))
@router.get("")
def history(mode:str|None=None,status:str|None=None,page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    q=select(PaperRecommendation).where(PaperRecommendation.user_id==u.id)
    if mode:q=q.where(PaperRecommendation.recommendation_mode==mode)
    if status:q=q.where(PaperRecommendation.status==status)
    rows=db.scalars(q.order_by(PaperRecommendation.updated_at.desc(),PaperRecommendation.id.desc()).offset((page-1)*page_size).limit(page_size)).all();return success_response({"items":[svc.serialize(x) for x in rows],"page":page,"page_size":page_size})
def owned(db,u,id):
    r=db.scalar(select(PaperRecommendation).where(PaperRecommendation.id==id,PaperRecommendation.user_id==u.id))
    if not r:raise HTTPException(404,"recommendation not found")
    return r
@router.patch("/{recommendation_id}/status")
def status(recommendation_id:int,p:RecommendationStatusRequest,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    r=owned(db,u,recommendation_id);r.status=p.status;db.commit();db.refresh(r);return success_response(svc.serialize(r))
@router.post("/{recommendation_id}/import")
def import_one(recommendation_id:int,db:Session=Depends(get_db),u:User=Depends(get_current_user)):return success_response(svc.import_recommendation(db,u.id,owned(db,u,recommendation_id)),"paper imported")
