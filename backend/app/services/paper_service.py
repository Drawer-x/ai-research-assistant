from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.paper import Paper


def get_owned_paper(db: Session, paper_id: int, user_id: int) -> Paper | None:
    return db.scalar(select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id))


def serialize_paper(paper: Paper, detail: bool = False) -> dict:
    data = {
        "paper_id": paper.id, "title": paper.title, "authors": paper.authors, "year": paper.year,
        "venue": paper.venue, "read_status": paper.read_status, "parse_status": paper.parse_status,
        "tags": [{"id": tag.id, "name": tag.name} for tag in paper.tags], "created_at": paper.created_at,
    }
    if detail:
        data.update({"abstract": paper.abstract, "pdf_path": paper.pdf_path, "updated_at": paper.updated_at,
                     "summaries": [{"id": s.id, "summary_type": s.summary_type, "content": s.content,
                                    "model_name": s.model_name, "is_mock": s.is_mock, "created_at": s.created_at}
                                   for s in paper.summaries]})
    return data
