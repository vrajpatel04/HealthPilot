from pydantic import BaseModel
from typing import Dict, List, Optional


class QueryRequest(BaseModel):
    query_text: str


class QueryResponse(BaseModel):
    query_text: str
    response_text: str
    sources: List[str]
