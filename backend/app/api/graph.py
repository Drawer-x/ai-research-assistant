from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import success_response
from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.graph_service import build_paper_graph

router = APIRouter(prefix="/graph", tags=["关系图 Mock"])


@router.get("/papers")
def paper_graph(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(build_paper_graph(db, current_user.id))
