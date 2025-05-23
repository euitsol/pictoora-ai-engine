from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.models.schemas import ErrorResponse

class APIException(Exception):
    def __init__(self, 
        status_code: int = 400,
        error_type: str = "generic_error",
        message: str = "An error occurred",
        code: int = 1000,
        details: dict = None
    ):
        self.status_code = status_code
        self.error_type = error_type
        self.message = message
        self.code = code
        self.details = details

async def api_exception_handler(request: Request, exc: APIException):
    error_response = ErrorResponse(
        error_type=exc.error_type,
        message=exc.message,
        code=exc.code,
        details=exc.details
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )