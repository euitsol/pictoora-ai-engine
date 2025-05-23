import uuid
from typing import Dict
from app.models.schemas import ProcessStatus, ProcessResponse
from app.config.settings import settings
from fastapi import BackgroundTasks
from app.utils.exceptions import APIException


class ProcessValidator:
    def validate(self, book_details: dict):
        message = []
        if not book_details.get("book_id") or not book_details.get("pages"):
            message.append(
                code="book_id",
                message="Invalid book details"
            )
        if not book_details.get("user_id"):
            message.append(
                code="user_id",
                message="Invalid user details"
            )
        if not book_details.get("pages"):
            message.append(
                code="pages",
                message="Invalid pages details"
            )
        if not book_details.get("pages").get("id"):
            message.append(
                code="pages.id",
                message="Invalid pages id"
            )
        if not book_details.get("pages").get("source_url"):
            message.append(
                code="pages.source_url",
                message="Invalid pages source_url"
            )
        if not book_details.get("pages").get("target_url"):
            message.append(
                code="pages.target_url",
                message="Invalid pages target_url"
            )
        if not book_details.get("pages").get("prompt"):
            message.append(
                code="pages.prompt",
                message="Invalid pages prompt"
            )
        if not book_details.get("pages").get("style"):
            message.append(
                code="pages.style",
                message="Invalid pages style"
            )
        
        if(message):    
            raise APIException(
                status_code=422,
                error_type="validation_error",
                messages=message,
                details={"book_details": book_details}
            )
            

class ProcessingService:
    def __init__(self):
        self.processes: Dict[str, dict] = {}
        self.book_store: Dict[str, dict] = {}

    async def start_processing(
        self,
        book_details: dict,
        image_url: str,
        background_tasks: BackgroundTasks
    ) -> ProcessResponse:
        process_id = str(uuid.uuid4())
        
        # Store initial process state
        self.processes[process_id] = {
            "status": ProcessStatus.PENDING,
            "book_id": book_details["book_id"],
            "pages": book_details["pages"]
        }
        
        # Add to book store if new
        if book_details["book_id"] not in self.book_store:
            self.book_store[book_details["book_id"]] = {
                "user_id": book_details["user_id"],
                "pages": []
            }
        
        # Add background task
        background_tasks.add_task(
            self._process_images,
            process_id,
            book_details,
            image_url
        )
        
        return ProcessResponse(
            process_id=process_id,
            status=ProcessStatus.PENDING
        )

    async def _process_images(self, process_id: str, book_details: dict, image_url: str):
        try:
            self.processes[process_id]["status"] = ProcessStatus.PROCESSING
            
            # Your image processing logic here
            # For demonstration, we'll just store the image URL
            for page in book_details["pages"]:
                # Simulate processing delay
                import time
                time.sleep(2)
                
                # Save result
                page_data = {
                    "page_id": page["id"],
                    "generated_url": image_url,
                    "status": "completed"
                }
                self.book_store[book_details["book_id"]]["pages"].append(page_data)
                
                # Call external API (mock example)
                # await self._call_external_api(book_details["book_id"], page["id"], image_url)
            
            self.processes[process_id]["status"] = ProcessStatus.COMPLETED
        except Exception as e:
            self.processes[process_id]["status"] = ProcessStatus.FAILED
            self.processes[process_id]["message"] = str(e)

    async def get_process_status(self, process_id: str) -> ProcessResponse:
        process = self.processes.get(process_id)
        if not process:
            return None
        return ProcessResponse(**process)

processing_service = ProcessingService()