from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AISummary(Base):
    __tablename__ = "ai_summaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), index=True)
    summary_type: Mapped[str] = mapped_column(String(50), default="structured")
    content: Mapped[str] = mapped_column(Text)
    model_name: Mapped[str] = mapped_column(String(100), default="mock")
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    paper = relationship("Paper", back_populates="summaries")
