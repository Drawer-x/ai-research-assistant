from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class PaperRecommendation(Base):
    __tablename__ = "paper_recommendations"
    __table_args__ = (UniqueConstraint("user_id", "provider", "external_id"), CheckConstraint("recommendation_mode in ('by_paper','for_library','by_topic')"), CheckConstraint("status in ('new','read_later','imported','not_interested')"))
    id: Mapped[int] = mapped_column(primary_key=True); user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(40)); external_id: Mapped[str] = mapped_column(String(255))
    seed_paper_ids_json: Mapped[str] = mapped_column(Text, default="[]"); recommendation_mode: Mapped[str] = mapped_column(String(30))
    paper_snapshot_json: Mapped[str] = mapped_column(Text); score: Mapped[float] = mapped_column(Float, default=0)
    reasons_json: Mapped[str] = mapped_column(Text, default="[]"); status: Mapped[str] = mapped_column(String(30), default="new")
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now()); updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
