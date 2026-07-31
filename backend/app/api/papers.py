import json
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.database import SessionLocal, get_db
from app.models.paper import Paper
from app.models.comparison import PaperComparison
from app.models.qa_record import QARecord
from app.models.summary import AISummary
from app.models.tag import Tag
from app.models.user import User
from app.schemas.ai import ComparePapersRequest, QARequest
from app.schemas.paper import PaperTagCreate, PaperUpdate, StatusUpdate, TagCreate
from app.services.ai_adapter_service import safe_answer_question, safe_compare_papers, safe_generate_summary
from app.services.paper_service import get_owned_paper, paper_with_relations, serialize_paper
from app.services.pdf_parser import extract_text_from_pdf
from app.services.text_splitter import split_text
from app.services.paper_content_service import PaperContentUnavailable, get_paper_analysis_content

router = APIRouter(tags=["文献与标签"])
logger = logging.getLogger(__name__)


def _build_vector_store(paper_id: int, user_id: int, full_text: str) -> None:
    """Best-effort background indexing; upload success does not depend on AI."""
    try:
        from app.services.embedding_service import get_embeddings
        from app.services.vector_store import delete_vector_store, save_vector_store

        chunks = split_text(full_text)
        embeddings = get_embeddings(chunks)
        if chunks and embeddings:
            with SessionLocal() as db:
                paper = db.scalar(select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id))
                if paper is None or (paper.full_text or "") != full_text:
                    return
            save_vector_store(
                paper_id,
                chunks,
                embeddings,
                owner_id=user_id,
                source_text=full_text,
            )
            with SessionLocal() as db:
                paper = db.scalar(select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id))
                if paper is None or (paper.full_text or "") != full_text:
                    delete_vector_store(paper_id, owner_id=user_id, source_text=full_text)
    except Exception:
        logger.exception("论文 %s 的向量索引生成失败", paper_id)


def owned_paper_or_error(db: Session, paper_id: int, user_id: int):
    paper = get_owned_paper(db, paper_id, user_id)
    return paper if paper else error_response("文献不存在或无权访问", 404)


def _load_json(value: str, default):
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


@router.post("/papers/upload")
def upload_paper(background_tasks: BackgroundTasks, file: UploadFile = File(...),
                 db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    filename = Path(file.filename or "").name
    if Path(filename).suffix.lower() != ".pdf":
        return error_response("只允许上传 PDF 文件")
    user_dir = settings.upload_path / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    destination = user_dir / f"{uuid4().hex}_{filename}"
    try:
        written = 0
        too_large = False
        with destination.open("wb") as output:
            while chunk := file.file.read(1024 * 1024):
                written += len(chunk)
                if written > settings.max_pdf_upload_bytes:
                    too_large = True
                    break
                output.write(chunk)
        if too_large:
            destination.unlink(missing_ok=True)
            return error_response("PDF 文件过大", 413)
    except OSError:
        destination.unlink(missing_ok=True)
        return error_response("文件保存失败", 500)
    finally:
        file.file.close()
    parsed = extract_text_from_pdf(str(destination))
    full_text = parsed.get("full_text", "")
    paper = Paper(
        user_id=current_user.id,
        title=parsed.get("title") or Path(filename).stem,
        authors=parsed.get("authors") or None,
        year=parsed.get("year"),
        venue=parsed.get("venue") or None,
        abstract=parsed.get("abstract") or None,
        pdf_path=str(destination.relative_to(settings.upload_path.parent)),
        full_text=full_text or None,
        parse_status="success" if full_text else "failed",
    )
    try:
        db.add(paper)
        db.commit()
        db.refresh(paper)
    except Exception as exc:
        db.rollback()
        destination.unlink(missing_ok=True)
        logger.error("用户 %s 的上传论文记录保存失败（%s）", current_user.id, type(exc).__name__)
        return error_response("文献记录保存失败", 500)
    if full_text:
        background_tasks.add_task(_build_vector_store, paper.id, current_user.id, full_text)
    return success_response(serialize_paper(paper, detail=True))


@router.get("/papers")
def list_papers(q: str | None = None, read_status: str | None = None, tag: str | None = None,
                db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    statement = paper_with_relations(select(Paper).where(Paper.user_id == current_user.id))
    if q:
        statement = statement.where(Paper.title.ilike(f"%{q}%"))
    if read_status:
        allowed = {"unread", "rough_read", "intensive_read", "to_reproduce", "for_review", "archived"}
        if read_status not in allowed:
            return error_response("无效的阅读状态")
        statement = statement.where(Paper.read_status == read_status)
    if tag:
        statement = statement.join(Paper.tags).where(Tag.name == tag)
    papers = db.scalars(statement.order_by(Paper.created_at.desc())).unique().all()
    return success_response([serialize_paper(p) for p in papers])


# Static routes must stay before /papers/{paper_id}.
@router.post("/papers/compare", tags=["AI 对比"])
def compare_papers(payload: ComparePapersRequest, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    papers = db.scalars(
        select(Paper).where(Paper.user_id == current_user.id, Paper.id.in_(payload.paper_ids))
    ).all()
    if len(papers) != len(payload.paper_ids):
        return error_response("部分文献不存在或无权访问", 404)
    paper_map = {paper.id: paper for paper in papers}
    ordered_papers = [paper_map[paper_id] for paper_id in payload.paper_ids]
    paper_data = [
        {
            "paper_id": paper.id,
            "title": paper.title,
            "authors": paper.authors,
            "year": paper.year,
            "venue": paper.venue,
            "abstract": paper.abstract,
            "full_text": paper.full_text or "",
        }
        for paper in ordered_papers
    ]
    result = safe_compare_papers(paper_data, payload.compare_dimensions)
    response_data = {
        "paper_ids": payload.paper_ids,
        "compare_dimensions": payload.compare_dimensions,
        **result,
    }
    record = PaperComparison(
        user_id=current_user.id,
        paper_ids_json=json.dumps(payload.paper_ids),
        compare_dimensions_json=json.dumps(payload.compare_dimensions, ensure_ascii=False),
        result_json=json.dumps(response_data, ensure_ascii=False),
        is_mock=bool(result["is_mock"]),
    )
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as exc:
        db.rollback()
        logger.error("用户 %s 的论文对比结果保存失败（%s）", current_user.id, type(exc).__name__)
        return error_response("论文对比成功，但保存失败", 500)
    response_data["comparison_id"] = record.id
    return success_response(response_data)


@router.get("/papers/comparisons", tags=["AI 对比"])
def comparison_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = db.scalars(
        select(PaperComparison)
        .where(PaperComparison.user_id == current_user.id)
        .order_by(PaperComparison.created_at.desc(), PaperComparison.id.desc())
    ).all()
    return success_response([
        {
            "id": record.id,
            "paper_ids": _load_json(record.paper_ids_json, []),
            "compare_dimensions": _load_json(record.compare_dimensions_json, []),
            "result": _load_json(record.result_json, {}),
            "is_mock": record.is_mock,
            "created_at": record.created_at,
        }
        for record in records
    ])


@router.get("/papers/{paper_id}")
def paper_detail(paper_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = owned_paper_or_error(db, paper_id, current_user.id)
    return paper if not isinstance(paper, Paper) else success_response(serialize_paper(paper, detail=True))


@router.put("/papers/{paper_id}")
def update_paper(paper_id: int, payload: PaperUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = owned_paper_or_error(db, paper_id, current_user.id)
    if not isinstance(paper, Paper): return paper
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(paper, key, value)
    db.commit(); db.refresh(paper)
    return success_response(serialize_paper(paper, detail=True))


@router.delete("/papers/{paper_id}")
def delete_paper(paper_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = owned_paper_or_error(db, paper_id, current_user.id)
    if not isinstance(paper, Paper): return paper
    db.delete(paper); db.commit()
    try:
        from app.services.vector_store import delete_vector_store

        delete_vector_store(paper_id)
    except Exception as exc:
        logger.error("论文 %s 的向量索引清理失败（%s）", paper_id, type(exc).__name__)
    return success_response({"paper_id": paper_id})


@router.put("/papers/{paper_id}/status")
def update_status(paper_id: int, payload: StatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = owned_paper_or_error(db, paper_id, current_user.id)
    if not isinstance(paper, Paper): return paper
    paper.read_status = payload.read_status.value
    db.commit()
    return success_response({"paper_id": paper.id, "read_status": paper.read_status})


@router.post("/tags")
def create_tag(payload: TagCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    name = payload.name.strip()
    if not name: return error_response("标签名不能为空")
    if db.scalar(select(Tag).where(Tag.user_id == current_user.id, Tag.name == name)):
        return error_response("标签名已存在", 409)
    tag = Tag(user_id=current_user.id, name=name); db.add(tag); db.commit(); db.refresh(tag)
    return success_response({"id": tag.id, "name": tag.name, "created_at": tag.created_at})


@router.get("/tags")
def list_tags(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tags = db.scalars(select(Tag).where(Tag.user_id == current_user.id).order_by(Tag.created_at.desc())).all()
    return success_response([{"id": t.id, "name": t.name, "created_at": t.created_at} for t in tags])


@router.post("/papers/{paper_id}/tags")
def add_tag(paper_id: int, payload: PaperTagCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = owned_paper_or_error(db, paper_id, current_user.id)
    if not isinstance(paper, Paper): return paper
    name = payload.tag_name.strip()
    if not name: return error_response("标签名不能为空")
    tag = db.scalar(select(Tag).where(Tag.user_id == current_user.id, Tag.name == name))
    if not tag:
        tag = Tag(user_id=current_user.id, name=name); db.add(tag); db.flush()
    if tag not in paper.tags: paper.tags.append(tag)
    db.commit(); db.refresh(tag)
    return success_response({"paper_id": paper.id, "tag": {"id": tag.id, "name": tag.name}})


@router.delete("/papers/{paper_id}/tags/{tag_id}")
def remove_tag(paper_id: int, tag_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = owned_paper_or_error(db, paper_id, current_user.id)
    if not isinstance(paper, Paper): return paper
    tag = db.scalar(select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id))
    if not tag or tag not in paper.tags: return error_response("论文未关联该标签", 404)
    paper.tags.remove(tag); db.commit()
    return success_response({"paper_id": paper.id, "tag_id": tag_id})


@router.post("/papers/{paper_id}/summary", tags=["AI 阅读"])
def create_summary(paper_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = owned_paper_or_error(db, paper_id, current_user.id)
    if not isinstance(paper, Paper): return paper
    try: content = get_paper_analysis_content(db, paper, current_user.id)
    except PaperContentUnavailable as exc: return error_response(str(exc), 422)
    result = safe_generate_summary(content["text"])
    summary = result["summary"]
    is_mock = result["is_mock"]
    model_name = result["model_name"]
    record = AISummary(
        paper_id=paper.id,
        content=json.dumps(summary, ensure_ascii=False),
        is_mock=is_mock,
        model_name=model_name,
    )
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as exc:
        db.rollback()
        logger.error("论文 %s 的总结保存失败（%s）", paper.id, type(exc).__name__)
        return error_response("总结生成成功，但保存失败", 500)
    return success_response({
        "paper_id": paper.id,
        "summary_id": record.id,
        "summary": summary,
        "is_mock": is_mock,
        "model_name": model_name,
        "analysis_scope": content["analysis_scope"],
    })


@router.get("/papers/{paper_id}/summaries", tags=["AI 阅读"])
def summary_history(paper_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = owned_paper_or_error(db, paper_id, current_user.id)
    if not isinstance(paper, Paper):
        return paper
    records = db.scalars(
        select(AISummary)
        .where(AISummary.paper_id == paper.id)
        .order_by(AISummary.created_at.desc(), AISummary.id.desc())
    ).all()
    return success_response([
        {
            "id": record.id,
            "paper_id": record.paper_id,
            "summary_type": record.summary_type,
            "content": _load_json(record.content, record.content),
            "model_name": record.model_name,
            "is_mock": record.is_mock,
            "created_at": record.created_at,
        }
        for record in records
    ])


@router.post("/papers/{paper_id}/qa", tags=["AI Mock"])
def paper_qa(paper_id: int, payload: QARequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = owned_paper_or_error(db, paper_id, current_user.id)
    if not isinstance(paper, Paper): return paper
    try: content = get_paper_analysis_content(db, paper, current_user.id)
    except PaperContentUnavailable as exc: return error_response(str(exc), 422)
    result = safe_answer_question(
        payload.question,
        content["text"],
        paper_id=paper.id,
        user_id=current_user.id,
    )
    record = QARecord(
        user_id=current_user.id,
        paper_id=paper.id,
        question=payload.question,
        answer=result["answer"],
        evidence_json=json.dumps(result["evidence"], ensure_ascii=False),
        has_evidence=result["has_evidence"],
        is_mock=result["is_mock"],
    )
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as exc:
        db.rollback()
        logger.error("论文 %s 的问答记录保存失败（%s）", paper.id, type(exc).__name__)
        return error_response("论文问答成功，但保存失败", 500)
    return success_response({**result, "qa_record_id": record.id, "analysis_scope": content["analysis_scope"]})


@router.get("/papers/{paper_id}/qa-records", tags=["AI 阅读"])
def qa_history(paper_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = owned_paper_or_error(db, paper_id, current_user.id)
    if not isinstance(paper, Paper):
        return paper
    records = db.scalars(
        select(QARecord)
        .where(QARecord.paper_id == paper.id, QARecord.user_id == current_user.id)
        .order_by(QARecord.created_at.desc(), QARecord.id.desc())
    ).all()
    return success_response([
        {
            "id": record.id,
            "paper_id": record.paper_id,
            "question": record.question,
            "answer": record.answer,
            "evidence": _load_json(record.evidence_json, []),
            "has_evidence": record.has_evidence,
            "is_mock": record.is_mock,
            "created_at": record.created_at,
        }
        for record in records
    ])
