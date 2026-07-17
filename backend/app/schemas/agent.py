from pydantic import BaseModel, Field, field_validator


class ResearchPlanRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    level: str = Field(default="beginner", min_length=1, max_length=50)
    duration_weeks: int = Field(default=4, ge=1, le=52)

    @field_validator("topic", "level")
    @classmethod
    def non_blank_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("字段不能为空")
        return cleaned
