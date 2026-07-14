import json
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.database import get_db
from app.models.paper import Paper
from app.models.summary import AISummary
from app.models.tag import Tag
from app.models.user import User
from app.schemas.ai import QARequest
from app.schemas.paper import PaperTagCreate, PaperUpdate, StatusUpdate, TagCreate
from app.services.ai_summary_service import generate_paper_summary
from app.services.paper_service import get_owned_paper, serialize_paper
from app.services.pdf_parser import extract_text_from_pdf
from app.services.text_splitter import split_text
from app.services.embedding_service import get_embeddings
from app.services.vector_store import save_vector_store
from app.services.qa_service import answer_question_about_paper

router = APIRouter(tags=["文献与标签"])


def owned_paper_or_error(db: Session, paper_id: int, user_id: int):
    paper = get_owned_paper(db, paper_id, user_id)
    return paper if paper else error_response("文献不存在或无权访问", 404)


@router.post("/papers/upload")
def upload_paper(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    filename = Path(file.filename or "").name
    if Path(filename).suffix.lower() != ".pdf":
        return error_response("只允许上传 PDF 文件")
    user_dir = settings.upload_path / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    destination = user_dir / f"{uuid4().hex}_{filename}"
    try:
        with destination.open("wb") as output:
            shutil.copyfileobj(file.file, output)
    except OSError:
        return error_response("文件保存失败", 500)
    parsed = extract_text_from_pdf(str(destination))
    full_text = parsed.get("full_text", "")
    paper = Paper(user_id=current_user.id, title=parsed.get("title") or Path(filename).stem,
                  abstract=parsed.get("abstract") or None, pdf_path=str(destination.relative_to(settings.upload_path.parent)),
                  full_text=full_text, parse_status="success" if full_text else "failed")
    db.add(paper)
    db.commit()
    db.refresh(paper)
    # =========================
    # RAG 向量库生成
    # =========================

    try:
        chunks = split_text(full_text)

        embeddings = get_embeddings(chunks)

        save_vector_store(
            paper.id,
            chunks,
            embeddings
        )

    except Exception as e:
        print("向量库生成失败:", e)


    return success_response(serialize_paper(paper, detail=True))


@router.get("/papers")
def list_papers(q: str | None = None, read_status: str | None = None, tag: str | None = None,
                db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    statement = select(Paper).options(selectinload(Paper.tags)).where(Paper.user_id == current_user.id)
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


@router.post("/papers/{paper_id}/summary", tags=["AI Mock"])
def create_summary(paper_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = owned_paper_or_error(db, paper_id, current_user.id)
    if not isinstance(paper, Paper): return paper
    summary = generate_paper_summary(paper.full_text or "")
    is_mock = bool(summary.pop("is_mock", False))
    record = AISummary(paper_id=paper.id, content=json.dumps(summary, ensure_ascii=False), is_mock=is_mock,
                       model_name="mock" if is_mock else "ecnu-max")
    db.add(record); db.commit()
    return success_response({"paper_id": paper.id, "summary": summary, "is_mock": is_mock})


@router.post("/papers/{paper_id}/qa", tags=["AI Mock"])
def paper_qa(paper_id: int, payload: QARequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = owned_paper_or_error(db, paper_id, current_user.id)
    if not isinstance(paper, Paper): return paper
    return success_response(answer_question_about_paper(payload.question, paper.full_text or "", paper_id=paper.id))
