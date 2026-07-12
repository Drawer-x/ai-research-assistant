from pydantic import BaseModel


class GraphNode(BaseModel):
    id: int
    name: str
    year: int | None = None
    category: str = "paper"


class GraphEdge(BaseModel):
    source: int
    target: int
    relation_type: str
    label: str
