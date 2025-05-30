from pydantic import BaseModel
from typing import Any, Optional, TypeVar, Generic, Dict

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: Optional[T] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True

class RootResponse(BaseResponse[dict]):
    pass

class HealthResponse(BaseResponse[dict]):
    pass

class ValidationError(BaseModel):
    field: str
    message: str

class ProcessStatus(BaseModel):
    process_id: str
    page_id: Optional[str] = None
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED
    url: Optional[str] = None  # URL of the processed image

class FileUploadResponse(BaseModel):
    file_path: str
    file_url: str

class UploadResponse(BaseResponse[FileUploadResponse]):
    pass

class InitProcessData(BaseModel):
    init_id: str
    status: Dict[str, Any] = {}

class InitiateProcessResponse(BaseResponse[InitProcessData]):
    pass

class ProcessBookResponse(BaseResponse[ProcessStatus]):
    pass

class ProcessStatusResponse(BaseResponse[list[ProcessStatus]]):
    pass 