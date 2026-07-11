from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.tag import paper_tags


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    authors: Mapped[str | None] = mapped_column(Text, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_path: Mapped[str] = mapped_column(String(1000))
    read_status: Mapped[str] = mapped_column(String(30), default="unread")
    parse_status: Mapped[str] = mapped_column(String(30), default="pending")
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="papers")
    tags = relationship("Tag", secondary=paper_tags, back_populates="papers")
    summaries = relationship("AISummary", back_populates="paper", cascade="all, delete-orphan")
