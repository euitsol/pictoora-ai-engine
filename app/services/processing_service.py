from typing import Dict, List, Any, Optional
from fastapi import status, BackgroundTasks
from app.utils.exceptions import APIException
from app.models.schemas import ProcessStatus, ProcessResponse, BookDetails, PageData
from pydantic import ValidationError
from app.utils.helpers import Helper

class ProcessValidator:
    @classmethod
    def validate_book_details(cls, book_details: Dict[str, Any]) -> BookDetails:
        try:
            cls.validate_book_id(book_details["book_id"])
            cls.validate_user_id(book_details["user_id"])
            book = BookDetails(**book_details)
            cls._validate_pages(book.pages)
            return book
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = ".".join(str(loc) for loc in error['loc'])
                errors.append({
                    "field": field,
                    "message": error['msg'],
                    "type": error['type']
                })
            
            raise APIException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error_type="validation_error",
                message="Invalid book details",
                details={"errors": errors}
            )
    
    @staticmethod
    def validate_book_id(book_id: str):
        if not book_id:
            raise APIException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error_type="validation_error",
                message="Book ID is required",
                code=2005
            )
    
    @staticmethod
    def validate_user_id(user_id: str):
        if not user_id:
            raise APIException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error_type="validation_error",
                message="User ID is required",
                code=2006
            )
    
    @staticmethod
    def validate_image_url(image_url: str):
        if not image_url or not image_url.startswith(('http://', 'https://')):
            raise APIException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error_type="validation_error",
                message="Invalid image URL",
                code=2007
            )
    
    @staticmethod
    def _validate_pages(pages: List[PageData]):
        if not pages:
            raise APIException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error_type="validation_error",
                message="At least one page is required",
                code=2001
            )
            
        for i, page in enumerate(pages):
            if not page.source_url.startswith(('http://', 'https://')):
                raise APIException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    error_type="validation_error",
                    message=f"Invalid URL format for page {i+1} source_url",
                    code=2002,
                    details={"field": f"pages.{i}.source_url"}
                )
                
            if not page.target_url.startswith(('http://', 'https://')):
                raise APIException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    error_type="validation_error",
                    message=f"Invalid URL format for page {i+1} target_url",
                    code=2003,
                    details={"field": f"pages.{i}.target_url"}
                )
                
            if len(page.prompt) < 10 or len(page.prompt) > 1000:
                raise APIException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    error_type="validation_error",
                    message=f"Prompt for page {i+1} must be between 10 and 1000 characters",
                    code=2004,
                    details={"field": f"pages.{i}.prompt"}
                )

class ProcessingService:
    def __init__(self):
        self.processes: Dict[str, Dict] = {}
        self.book_store: Dict[str, Dict] = {}
    
    async def start_processing(
        self,
        book_details: Dict[str, Any],
        background_tasks: BackgroundTasks,
        image_url: str = None
    ) -> ProcessResponse:
        validated_book = ProcessValidator.validate_book_details(book_details)
        process_id = Helper.generate_process_id()
        
        self.processes[process_id] = {
            "status": ProcessStatus.PENDING,
            "book_id": validated_book.book_id,
            "pages": [page.model_dump() for page in validated_book.pages]
        }
        
        if validated_book.book_id not in self.book_store:
            self.book_store[validated_book.book_id] = {
                "user_id": validated_book.user_id,
                "pages": []
            }
        
        background_tasks.add_task(
            self._process_images,
            process_id,
            validated_book.model_dump(),
            image_url
        )
        
        return ProcessResponse(
            process_id=process_id,
            status=ProcessStatus.PENDING,
            message="Processing started"
        )
    
    async def _process_images(self, process_id: str, book_details: Dict, image_url: str = None):
        try:
            self.processes[process_id]["status"] = ProcessStatus.PROCESSING
            
            for page in book_details["pages"]:
                import time
                time.sleep(2)
                
                page_data = {
                    "page_id": page["id"],
                    "generated_url": image_url or f"https://example.com/generated/{page['id']}",
                    "status": "completed"
                }
                
                self.book_store[book_details["book_id"]]["pages"].append(page_data)
            
            self.processes[process_id]["status"] = ProcessStatus.COMPLETED
            
        except Exception as e:
            self.processes[process_id]["status"] = ProcessStatus.FAILED
            self.processes[process_id]["message"] = str(e)
    
    async def get_process_status(self, process_id: str) -> Optional[ProcessResponse]:
        process = self.processes.get(process_id)
        if not process:
            return None
            
        return ProcessResponse(
            process_id=process_id,
            status=process["status"],
            message=process.get("message")
        )

# Singleton instance
processing_service = ProcessingService()