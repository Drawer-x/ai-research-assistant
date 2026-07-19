import json
import logging
import time

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.config import settings
from app.core.security import get_current_user
from app.database import get_db
from app.models.research_plan import ResearchPlan
from app.models.paper import Paper
from app.models.user import User
from app.schemas.agent import ResearchPlanRequest
from app.services.agent_adapter_service import safe_generate_research_plan

router = APIRouter(prefix="/agent", tags=["Agent Mock"])
logger = logging.getLogger(__name__)


@router.post("/research-plan")
def research_plan(payload: ResearchPlanRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    started = time.monotonic()
    logger.info("Agent API 请求进入（API key configured=%s, upstream_timeout=%s）", bool(settings.ecnu_api_key), settings.ecnu_api_timeout_seconds)
    papers = list(db.scalars(select(Paper).where(
        Paper.user_id == current_user.id, Paper.id.in_(payload.paper_ids)
    )).all()) if payload.paper_ids else []
    if len(papers) != len(payload.paper_ids):
        return error_response("部分文献不存在或无权访问", 404)
    paper_data = [{"paper_id": p.id, "title": p.title, "abstract": p.abstract,
                   "full_text": (p.full_text or "")[:4000]} for p in papers]
    result = safe_generate_research_plan(payload.topic, payload.research_goal, payload.duration_weeks, payload.level, paper_data)
    content = {"research_topic": payload.topic, "research_goal": payload.research_goal,
               "duration_weeks": payload.duration_weeks, "current_level": payload.level,
               "paper_ids": payload.paper_ids, **result}
    record = ResearchPlan(
        user_id=current_user.id,
        topic=payload.topic,
        goal=payload.research_goal or f"{payload.level} level research plan",
        plan_content=json.dumps(content, ensure_ascii=False),
        is_mock=bool(result.get("is_mock", True)),
    )
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as exc:
        db.rollback()
        logger.error("用户 %s 的科研计划保存失败（%s）", current_user.id, type(exc).__name__)
        return error_response("科研计划生成成功，但保存失败", 500)
    logger.info("Agent API 完成（elapsed_ms=%d, is_mock=%s）", int((time.monotonic() - started) * 1000), record.is_mock)
    return success_response({"plan_id": record.id, **content, "created_at": record.created_at})


def _load_plan(record: ResearchPlan) -> dict:
    try:
        content = json.loads(record.plan_content)
        if not isinstance(content, dict): content = {}
    except (TypeError, json.JSONDecodeError):
        content = {}
    return {"plan_id": record.id, "research_topic": content.get("research_topic", record.topic),
            "research_goal": content.get("research_goal", record.goal or ""),
            "duration_weeks": content.get("duration_weeks", len(content.get("weekly_plan", []))),
            "current_level": content.get("current_level"),
            "paper_ids": content.get("paper_ids", []),
            "reading_route": content.get("reading_route", []), "stages": content.get("stages", []),
            "weekly_plan": content.get("weekly_plan", []), "tasks": content.get("tasks", []),
            "risks": content.get("risks", []), "recommended_papers": content.get("recommended_papers", []),
            "is_mock": record.is_mock, "created_at": record.created_at}


@router.get("/research-plans")
def plan_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = db.scalars(select(ResearchPlan).where(ResearchPlan.user_id == current_user.id)
                         .order_by(ResearchPlan.created_at.desc(), ResearchPlan.id.desc())).all()
    return success_response([_load_plan(record) for record in records])


@router.get("/research-plans/{plan_id}")
def plan_detail(plan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.scalar(select(ResearchPlan).where(ResearchPlan.id == plan_id, ResearchPlan.user_id == current_user.id))
    return success_response(_load_plan(record)) if record else error_response("科研计划不存在或无权访问", 404)
