from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from app.core.response import success_response
from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.discovery import DiscoveryImportRequest
from app.services.discovery_service import get_external_paper,import_external_paper,search_external_papers
router=APIRouter(prefix="/discovery",tags=["Discovery"])
@router.get("/search")
def search(query:str=Query(min_length=2),year_from:int|None=None,year_to:int|None=None,open_access:bool|None=None,page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if year_from and year_to and year_from>year_to: from fastapi import HTTPException; raise HTTPException(422,"year_from must not exceed year_to")
    return success_response(search_external_papers(db,user.id,query=query,year_from=year_from,year_to=year_to,open_access=open_access,page=page,page_size=page_size))
@router.get("/papers/{external_id}")
def detail(external_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)): return success_response(get_external_paper(db,user.id,external_id))
@router.post("/import")
def import_paper(payload:DiscoveryImportRequest,db:Session=Depends(get_db),user:User=Depends(get_current_user)): return success_response(import_external_paper(db,user.id,payload.provider,payload.external_id),"paper imported")
