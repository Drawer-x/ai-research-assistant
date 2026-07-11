from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ReadStatus(str, Enum):
    unread = "unread"
    rough_read = "rough_read"
    intensive_read = "intensive_read"
    to_reproduce = "to_reproduce"
    for_review = "for_review"
    archived = "archived"


class PaperUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    authors: str | None = None
    year: int | None = Field(default=None, ge=0, le=9999)
    venue: str | None = None
    abstract: str | None = None


class StatusUpdate(BaseModel):
    read_status: ReadStatus


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class PaperTagCreate(BaseModel):
    tag_name: str = Field(min_length=1, max_length=100)


class TagInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    created_at: datetime
