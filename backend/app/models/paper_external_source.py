from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class PaperExternalSource(Base):
    __tablename__ = "paper_external_sources"
    __table_args__ = (UniqueConstraint("user_id", "provider", "external_id"), UniqueConstraint("paper_id"), Index("ix_external_provider_id", "provider", "external_id"))
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(40)); external_id: Mapped[str] = mapped_column(String(255))
    doi: Mapped[str|None] = mapped_column(String(255)); arxiv_id: Mapped[str|None] = mapped_column(String(255))
    external_url: Mapped[str|None] = mapped_column(Text); pdf_url: Mapped[str|None] = mapped_column(Text)
    abstract: Mapped[str|None] = mapped_column(Text); citation_count: Mapped[int] = mapped_column(Integer, default=0)
    reference_count: Mapped[int] = mapped_column(Integer, default=0); fields_of_study_json: Mapped[str] = mapped_column(Text, default="[]")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
