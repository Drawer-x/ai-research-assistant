from pydantic import BaseModel, Field


class ResearchPlanRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    level: str = Field(default="beginner", min_length=1, max_length=50)
    duration_weeks: int = Field(default=4, ge=1, le=52)
