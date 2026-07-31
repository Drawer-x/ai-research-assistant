from pydantic import BaseModel, Field, field_validator


class GraphGenerateRequest(BaseModel):
    paper_ids: list[int] = Field(default_factory=list, max_length=200)
    relation_types: list[str] = Field(
        default_factory=lambda: ["topic_similarity", "method_similarity"]
    )
    force_regenerate: bool = False

    @field_validator("paper_ids")
    @classmethod
    def valid_ids(cls, value: list[int]) -> list[int]:
        if any(isinstance(item, bool) or item <= 0 for item in value) or len(set(value)) != len(value):
            raise ValueError("paper_ids 必须是唯一正整数")
        return value

    @field_validator("relation_types")
    @classmethod
    def valid_relation_types(cls, value: list[str]) -> list[str]:
        allowed = {"citation", "topic_similarity", "method_similarity"}
        cleaned = [item.strip() for item in value]
        if not cleaned or set(cleaned) - allowed or len(set(cleaned)) != len(cleaned):
            raise ValueError("relation_types 无效或重复")
        return cleaned


class GraphNode(BaseModel):
    id: int
    name: str
    year: int | None = None
    category: str = "paper"
    paper_id: int | None = None
    title: str | None = None
    authors: str | None = None
    venue: str | None = None
    read_status: str | None = None


class GraphEdge(BaseModel):
    id: int | None = None
    source: int
    target: int
    relation_type: str
    label: str
    relation_reason: str | None = None
    confidence: float | None = None
    inferred: bool = False
    weight: float | None = None
    description: str | None = None
    is_mock: bool = False

class GraphExpandRequest(BaseModel):
    node_id: str
    expand_type: str
    limit: int = Field(10, ge=1, le=50)
