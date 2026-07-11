from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ResearchPlan(Base):
    __tablename__ = "research_plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic: Mapped[str] = mapped_column(String(500))
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_content: Mapped[str] = mapped_column(Text)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    user = relationship("User", back_populates="research_plans")
