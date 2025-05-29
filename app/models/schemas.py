from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class ProcessStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class PageData(BaseModel):
    id: int
    source_url: str
    target_url: str
    prompt: str
    style: str
    status: ProcessStatus = ProcessStatus.PENDING

class BookDetails(BaseModel):
    user_id: str
    book_id: str
    pages: List[PageData]

class ProcessResponse(BaseModel):
    process_id: str
    status: ProcessStatus
    message: Optional[str] = None
    output_url: Optional[str] = None
    
class ErrorResponse(BaseModel):
    error_type: str = Field(..., example="validation_error")
    message: str = Field(..., example="Invalid file format")
    code: int = Field(..., example=1001)
    details: Optional[Dict[str, Any]] = Field(None, example={"allowed_formats": ["jpg", "png"]})
    