import base64
import tempfile
import uuid
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import status, BackgroundTasks
from openai import OpenAI
from PIL import Image
from pydantic import ValidationError

from app.config import settings
from app.models.schemas import ProcessStatus, ProcessResponse, BookDetails, PageData
from app.utils.exceptions import APIException
from app.utils.helpers import Helper

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Configure output directory
OUTPUT_DIR = Path(settings.IMAGE_OUTPUT_DIR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
    
    def _prepare_image(self, image_path: str) -> str:
        """Download and prepare image for processing"""
        # In a real implementation, you would download the image from the URL here
        # For now, we'll assume the path is already local
        try:
            img = Image.open(image_path).convert("RGBA")
            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            img.save(temp_file, format="PNG")
            temp_file.close()
            return temp_file.name
        except Exception as e:
            raise APIException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error_type="image_processing_error",
                message=f"Failed to process image: {str(e)}",
                code=3001
            )

    async def _process_images(self, process_id: str, book_details: Dict, image_url: str = None):
        try:
            self.processes[process_id]["status"] = ProcessStatus.PROCESSING
            
            for page in book_details["pages"]:
                page_id = page["id"]
                try:
                    # Prepare source and target images
                    source_temp = self._prepare_image(page["source_url"])
                    target_temp = self._prepare_image(page["target_url"])

                    # Generate face swap prompt
                    prompt_edit = (
                        f"PRECISE FACE SWAP: {page['prompt']}\n"
                        f"Style: {page['style']}\n"
                        "Maintain the source image's head position, lighting, and background. "
                        "Seamlessly blend the face edges. Preserve all non-facial elements exactly."
                    )

                    # Generate the face-swapped image
                    with open(source_temp, "rb") as src_file, open(target_temp, "rb") as tgt_file:
                        response = client.images.edit(
                            model="gpt-image-1",
                            image=[src_file, tgt_file],
                            prompt=prompt_edit,
                            size="1024x1024",
                        )

                    # Save the result with relative path for URL
                    output_filename = f"{uuid.uuid4()}.png"
                    output_path = OUTPUT_DIR / output_filename
                    
                    with output_path.open("wb") as f:
                        f.write(base64.b64decode(response.data[0].b64_json))
                    
                    # Store relative path for URL
                    relative_output_path = output_path.relative_to(settings.STORAGE_PATH)
                    
                    # Update page data with result
                    page_data = {
                        "page_id": page_id,
                        "generated_url": f"/{relative_output_path.as_posix()}",
                        "status": ProcessStatus.COMPLETED
                    }
                    
                    self.book_store[book_details["book_id"]]["pages"].append(page_data)
                    
                except Exception as e:
                    error_msg = str(e)
                    page_data = {
                        "page_id": page_id,
                        "error": error_msg,
                        "status": ProcessStatus.FAILED
                    }
                    self.book_store[book_details["book_id"]]["pages"].append(page_data)
                    
                    # Continue processing other pages even if one fails
                    continue
                    
                finally:
                    # Clean up temporary files
                    if 'source_temp' in locals() and Path(source_temp).exists():
                        Path(source_temp).unlink(missing_ok=True)
                    if 'target_temp' in locals() and Path(target_temp).exists():
                        Path(target_temp).unlink(missing_ok=True)
            
            # Update process status
            self.processes[process_id]["status"] = ProcessStatus.COMPLETED
            
        except Exception as e:
            self.processes[process_id]["status"] = ProcessStatus.FAILED
            self.processes[process_id]["message"] = str(e)
    
    async def get_process_status(self, process_id: str) -> Optional[ProcessResponse]:
        process = self.processes.get(process_id)
        if not process:
            return None
            
        # Get the latest page result if available
        output_url = None
        if process["status"] == ProcessStatus.COMPLETED and "book_id" in process:
            book_id = process["book_id"]
            if book_id in self.book_store and self.book_store[book_id]["pages"]:
                # Get the latest processed page
                latest_page = self.book_store[book_id]["pages"][-1]
                if latest_page.get("status") == ProcessStatus.COMPLETED:
                    output_url = latest_page.get("generated_url")
        
        return ProcessResponse(
            process_id=process_id,
            status=process["status"],
            message=process.get("message"),
            output_url=output_url
        )

# Singleton instance
processing_service = ProcessingService()