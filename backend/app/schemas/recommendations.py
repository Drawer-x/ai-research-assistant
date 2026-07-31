from typing import Literal
from pydantic import BaseModel,Field,model_validator
class ByPaperRequest(BaseModel): paper_id:int; limit:int=Field(20,ge=1,le=100)
class ForLibraryRequest(BaseModel): paper_ids:list[int]=Field(min_length=1,max_length=5); limit:int=Field(20,ge=1,le=100)
class ByTopicRequest(BaseModel):
    topic:str=Field(min_length=2); year_from:int|None=None; year_to:int|None=None; limit:int=Field(20,ge=1,le=100)
    @model_validator(mode="after")
    def years(self):
        if self.year_from and self.year_to and self.year_from>self.year_to: raise ValueError("invalid year range")
        return self
class RecommendationStatusRequest(BaseModel): status:Literal["new","read_later","imported","not_interested"]
