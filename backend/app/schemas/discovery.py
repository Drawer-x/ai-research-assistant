from pydantic import BaseModel, Field
class DiscoveryImportRequest(BaseModel):
    provider:str="semantic_scholar"
    external_id:str=Field(min_length=1,max_length=255)
