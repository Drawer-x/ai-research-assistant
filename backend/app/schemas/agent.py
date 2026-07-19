from pydantic import BaseModel, Field, field_validator, model_validator


class ResearchPlanRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    level: str = Field(default="beginner", min_length=1, max_length=50)
    duration_weeks: int = Field(default=4, ge=1, le=52)
    research_goal: str = Field(default="", max_length=2000)
    paper_ids: list[int] = Field(default_factory=list, max_length=100)

    @model_validator(mode="before")
    @classmethod
    def compatible_names(cls, value):
        if isinstance(value, dict):
            value = dict(value)
            value.setdefault("topic", value.get("research_topic"))
            value.setdefault("level", value.get("current_level", "beginner"))
        return value

    @field_validator("topic", "level")
    @classmethod
    def non_blank_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("字段不能为空")
        return cleaned

    @field_validator("paper_ids")
    @classmethod
    def valid_paper_ids(cls, value: list[int]) -> list[int]:
        if any(isinstance(item, bool) or item <= 0 for item in value) or len(set(value)) != len(value):
            raise ValueError("paper_ids 必须是唯一正整数")
        return value
