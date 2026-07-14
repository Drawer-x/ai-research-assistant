import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import success_response
from app.core.security import get_current_user
from app.database import get_db
from app.models.research_plan import ResearchPlan
from app.models.user import User
from app.schemas.agent import ResearchPlanRequest
from app.services.agent_service import generate_research_plan

router = APIRouter(prefix="/agent", tags=["Agent Mock"])


@router.post("/research-plan")
def research_plan(payload: ResearchPlanRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = generate_research_plan(payload.topic, payload.level, payload.duration_weeks)
    record = ResearchPlan(user_id=current_user.id, topic=payload.topic, goal=f"{payload.level} level research plan",
                          plan_content=json.dumps(result, ensure_ascii=False), is_mock=result.get("is_mock", True))
    db.add(record); db.commit()
    return success_response(result)
