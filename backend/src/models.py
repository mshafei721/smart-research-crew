from pydantic import BaseModel, Field
from typing import List, Optional

class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=100)
    guidelines: str = Field("", max_length=1000)
    sections: str = Field(..., min_length=3, max_length=500)

class ResearchSection(BaseModel):
    content: str
    sources: List[str]

class Report(BaseModel):
    topic: str
    sections: List[ResearchSection]
    references: List[str]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

class SettingsResponse(BaseModel):
    llm_model: str
    max_concurrent_tasks: int
    cache_enabled: bool
