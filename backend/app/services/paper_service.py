"""Queries and response serialization for papers."""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models.paper import Paper


def paper_with_relations(statement: Select, *, include_summaries: bool = False) -> Select:
    options = [selectinload(Paper.tags)]
    if include_summaries:
        options.append(selectinload(Paper.summaries))
    return statement.options(*options)


def get_owned_paper(db: Session, paper_id: int, user_id: int) -> Paper | None:
    statement = paper_with_relations(
        select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id),
        include_summaries=True,
    )
    return db.scalar(statement)


def serialize_paper(paper: Paper, detail: bool = False) -> dict:
    data = {
        "paper_id": paper.id,
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.year,
        "venue": paper.venue,
        "read_status": paper.read_status,
        "parse_status": paper.parse_status,
        "tags": [{"id": tag.id, "name": tag.name} for tag in paper.tags],
        "created_at": paper.created_at,
    }
    if detail:
        data.update(
            abstract=paper.abstract,
            pdf_path=paper.pdf_path,
            updated_at=paper.updated_at,
            summaries=[
                {
                    "id": summary.id,
                    "summary_type": summary.summary_type,
                    "content": summary.content,
                    "model_name": summary.model_name,
                    "is_mock": summary.is_mock,
                    "created_at": summary.created_at,
                }
                for summary in sorted(
                    paper.summaries,
                    key=lambda item: (item.created_at is not None, item.created_at),
                    reverse=True,
                )
            ],
        )
    return data
