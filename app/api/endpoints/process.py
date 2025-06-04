from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
from ...schemas.responses import InitiateProcessResponse, ProcessBookResponse, ProcessStatusResponse, ProcessStatus, InitProcessData
from ...core.cache import cache
from ...core.config import settings
from ...core.logger import get_logger
import os
from openai import OpenAI
import base64
from pathlib import Path
import tempfile
from ...core.masking import mask_child_face
from PIL import Image

logger = get_logger()
router = APIRouter()

class ProcessBookRequest(BaseModel):
    init_id: str
    source_url: str
    target_url: str
    prompt: Dict[str, Any]

class ProcessStatusRequest(BaseModel):
    process_id: str
    page_id: Optional[str] = None

class PromptTemplate:
    """A class to manage and render prompt templates."""
    
    # Define the default template
    DEFAULT_TEMPLATE = """
    {prompt}
    """
    
    @classmethod
    def render(cls, prompt_data: Dict[str, Any]) -> str:
        """Render the prompt template with the provided data."""
        custom_prompt = prompt_data.get('prompt', 'A professional headshot with natural lighting and neutral background')
        
        # Render full prompt
        return cls.DEFAULT_TEMPLATE.format(prompt=custom_prompt).strip()

def convert_to_rgba(image_path: str, is_base64: bool = False) -> str:
    """Convert image to RGBA format and save to temporary file"""
    try:
        if image_path.startswith(('http://', 'https://')):
            image_path = image_path.split('/uploads/')[-1]
            image_path = os.path.join(settings.UPLOAD_DIR, image_path)
        
        # Ensure the file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        img = Image.open(image_path).convert("RGBA")
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(temp_file, format="PNG")
        temp_file.close()  # Close file for later reopening
        
        if is_base64:
            with open(temp_file.name, 'rb') as f:
                return base64.b64encode(f.read()).decode("utf-8")
        return temp_file.name
    except Exception as e:
        logger.error(f"Image conversion failed: {str(e)}")
        if 'temp_file' in locals() and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise

async def process_image_background(process_id: str, page_id: str, source_url: str, target_url: str, prompt: Dict[str, Any]):
    source_temp = None
    target_temp = None
    source_masked_temp = None
    
    try:
        # Generate the prompt using the template
        actual_prompt = PromptTemplate.render(prompt)
                
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Get existing cache data or initialize if missing
        process_data = cache.get(process_id) or {}
        process_data[page_id] = {"status": "PROCESSING", "url": None}
        cache.set(process_id, process_data, expire=3600)  # Reset TTL on update
        
        # Convert images to RGBA format
        source_temp = convert_to_rgba(source_url)
        target_temp = convert_to_rgba(target_url)
        
        # Mask the source image
        source_masked_temp = mask_child_face(source_temp)
        logger.info(f"Masked image: {source_masked_temp}")
        
        # Process the image
        with open(source_temp, "rb") as src_file, \
             open(source_masked_temp, "rb") as masked_file, \
             open(target_temp, "rb") as tgt_file:
            
            response = client.images.edit(
                model="gpt-image-1",
                image=[src_file, masked_file, tgt_file],
                prompt=actual_prompt,
                size="1024x1024",
                quality="high",
                n=1
            )
            
            # Save the result
            image_data = base64.b64decode(response.data[0].b64_json)
            new_filename = f"p_{page_id}_{uuid.uuid4()}_result.webp"
            output_path = os.path.join(settings.UPLOAD_DIR, new_filename)
            
            
            with open(output_path, "wb") as f:
                f.write(image_data)
            
            # Generate file URL with API_V1_STR prefix
            file_url = f"{settings.APP_URL}/storage/uploads/{new_filename}"
            relative_path = str(Path("storage/uploads") / new_filename)
            
            # Update status to completed with URL
            process_data = cache.get(process_id)  # Re-fetch to handle concurrent updates
            if process_data is None:
                process_data = {}
            process_data[page_id] = {"status": "COMPLETED", "url": file_url}
            cache.set(process_id, process_data, expire=3600)
            
        # Clean up temporary files
        for temp_file in [source_temp, target_temp, source_masked_temp]:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            
    except Exception as e:
        logger.error(f"Image processing failed: {str(e)}")
        process_data = cache.get(process_id)
        if process_data is None:
            process_data = {}
        process_data[page_id] = {"status": "FAILED", "url": None}
        cache.set(process_id, process_data, expire=3600)  # Reset TTL on failure
        
        # Clean up temporary files on error
        for temp_file in [source_temp, target_temp, source_masked_temp]:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)

@router.post("/initiate-process", response_model=InitiateProcessResponse)
async def initiate_process():
    """Initiate a new process and return a unique ID"""
    try:
        init_id = str(uuid.uuid4())
        cache.set(init_id, {}, expire=3600)  # Expire after 1 hour
        logger.info(f"Process initiated with ID: {init_id}")
        return InitiateProcessResponse(
            status_code=3000,
            message="Process initiated successfully",
            data=InitProcessData(init_id=init_id, status={})
        )
    except Exception as e:
        logger.error(f"Process initiation failed: {str(e)}")
        return InitiateProcessResponse(
            status_code=3001,
            message="Process initiation failed",
            error=str(e)
        )

@router.post("/process/book", response_model=ProcessBookResponse)
async def process_book(request: ProcessBookRequest, background_tasks: BackgroundTasks):
    """Process a book with the given parameters"""
    try:
        # Validate init_id exists in cache
        existing_cache = cache.get(request.init_id)
        if existing_cache is None:
            raise HTTPException(status_code=400, detail="Invalid init_id")
        
        # Generate only a new page_id
        page_id = str(uuid.uuid4())
        
        # Update existing cache with new page data
        existing_cache[page_id] = {"status": "PENDING", "url": None}
        cache.set(request.init_id, existing_cache, expire=3600)
        
        background_tasks.add_task(
            process_image_background,
            request.init_id,  # Use init_id instead of process_id
            page_id,
            request.source_url,
            request.target_url,
            request.prompt
        )
        
        logger.info(f"Book processing started: {request.init_id}, page: {page_id}")
        return ProcessBookResponse(
            status_code=4000,
            message="Processing started",
            data=ProcessStatus(
                process_id=request.init_id,
                page_id=page_id,
                status="PENDING",
                url=None
            )
        )
    except Exception as e:
        logger.error(f"Book processing failed: {str(e)}")
        return ProcessBookResponse(
            status_code=4001,
            message="Processing failed",
            error=str(e)
        )

@router.post("/process/status", response_model=ProcessStatusResponse)
async def get_process_status(request: ProcessStatusRequest):
    """Get the status of a process"""
    try:
        process_data = cache.get(request.process_id)
        if process_data is None:
            raise HTTPException(status_code=404, detail="Process not found")
        
        if request.page_id:
            if request.page_id not in process_data:
                raise HTTPException(status_code=404, detail="Page not found")
            page_data = process_data[request.page_id]
            if isinstance(page_data, str):
                # Handle old format where only status was stored
                status = page_data
                url = None
            else:
                # Handle new format with status and url
                status = page_data.get("status", "UNKNOWN")
                url = page_data.get("url")
            
            statuses = [ProcessStatus(
                process_id=request.process_id,
                page_id=request.page_id,
                status=status,
                url=url
            )]
        else:
            statuses = []
            for page_id, page_data in process_data.items():
                if isinstance(page_data, str):
                    # Handle old format where only status was stored
                    status = page_data
                    url = None
                else:
                    # Handle new format with status and url
                    status = page_data.get("status", "UNKNOWN")
                    url = page_data.get("url")
                
                statuses.append(ProcessStatus(
                    process_id=request.process_id,
                    page_id=page_id,
                    status=status,
                    url=url
                ))
        
        logger.info(f"Status retrieved for process: {request.process_id}")
        return ProcessStatusResponse(
            status_code=5000,
            message="Status retrieved successfully",
            data=statuses
        )
    except Exception as e:
        logger.error(f"Status retrieval failed: {str(e)}")
        return ProcessStatusResponse(
            status_code=5001,
            message="Status retrieval failed",
            error=str(e)
        )