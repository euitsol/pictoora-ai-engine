from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import base64
import os
import requests
import random
import aiofiles
import aiohttp
import asyncio
from pathlib import Path
from ...schemas.responses import InitiateProcessResponse, ProcessBookResponse, ProcessStatusResponse, ProcessStatus, InitProcessData
from ...core.cache import cache
from ...core.config import settings
from ...core.logger import get_logger

logger = get_logger()
router = APIRouter()

# Helper functions for image conversion
async def image_file_to_base64(image_path: str) -> str:
    async with aiofiles.open(image_path, 'rb') as f:
        image_data = await f.read()
    return base64.b64encode(image_data).decode('utf-8')

async def image_url_to_base64(image_url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            image_data = await response.read()
            return base64.b64encode(image_data).decode('utf-8')

async def resolve_image_to_base64(image_ref: str) -> str:
    if image_ref.startswith(('http://', 'https://')):
        return await image_url_to_base64(image_ref)
    else:
        full_path = os.path.join(settings.UPLOAD_DIR, image_ref)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Image not found: {full_path}")
        return await image_file_to_base64(full_path)

class ProcessBookRequest(BaseModel):
    init_id: str
    source_url: str
    target_url: str
    prompt: Dict[str, Any]

class ProcessStatusRequest(BaseModel):
    process_id: str
    page_id: Optional[str] = None

class PromptTemplate:
    DEFAULT_TEMPLATE = """
    {prompt}
    """
    
    @classmethod
    def render(cls, prompt_data: Dict[str, Any]) -> str:
        custom_prompt = prompt_data.get('prompt', 'A professional headshot with natural lighting and neutral background')
        return cls.DEFAULT_TEMPLATE.format(prompt=custom_prompt).strip()

async def process_image_background(process_id: str, page_id: str, source_url: str, target_url: str, prompt: Dict[str, Any]):
    try:
        logger.info(f"Starting background task for {process_id}/{page_id}")
        
        # Get existing cache data
        process_data = cache.get(process_id) or {}
        process_data[page_id] = {"status": "PROCESSING", "url": None}
        cache.set(process_id, process_data, expire=3600)
        
        # Convert images to base64 asynchronously
        source_base64, target_base64 = await asyncio.gather(
            resolve_image_to_base64(source_url),
            resolve_image_to_base64(target_url)
        )
        
        # Prepare Segmind API request
        segmind_data = {
            "source_image": target_base64,
            "target_image": source_base64,
            "face_strength": 0.8,
            "style_strength": 0.8,
            "seed": random.randint(1, 1000000),
            "steps": 10,
            "cfg": 1.5,
            "output_format": "png",
            "output_quality": 95,
            "base64": False
        }
        
        # Make async HTTP request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                settings.SEGMIND_API_URL,
                json=segmind_data,
                headers={'x-api-key': settings.SEGMIND_API_KEY},
                timeout=100
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Segmind API error: {response.status} - {error_text[:200]}")
                    raise HTTPException(status_code=500, detail="External API error")
                
                image_data = await response.read()
        
        # Save the result
        new_filename = f"p_{page_id}_{uuid.uuid4()}_result.png"
        output_path = os.path.join(settings.UPLOAD_DIR, new_filename)
        
        async with aiofiles.open(output_path, "wb") as f:
            await f.write(image_data)
        
        # Generate file URL
        file_url = f"{settings.APP_URL}/storage/uploads/{new_filename}"
        
        # Update cache
        process_data = cache.get(process_id) or {}
        process_data[page_id] = {"status": "COMPLETED", "url": file_url}
        cache.set(process_id, process_data, expire=3600)
        
        logger.info(f"Completed background task for {process_id}/{page_id}")
        
    except asyncio.TimeoutError:
        logger.error("Segmind API request timed out")
        process_data = cache.get(process_id) or {}
        process_data[page_id] = {"status": "FAILED", "url": None, "error": "API timeout"}
        cache.set(process_id, process_data, expire=3600)
    except Exception as e:
        logger.error(f"Background task failed: {str(e)}", exc_info=True)
        process_data = cache.get(process_id) or {}
        process_data[page_id] = {"status": "FAILED", "url": None, "error": str(e)}
        cache.set(process_id, process_data, expire=3600)
        
        
@router.post("/initiate-process", response_model=InitiateProcessResponse)
async def initiate_process():
    try:
        init_id = str(uuid.uuid4())
        cache.set(init_id, {}, expire=3600)
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
    try:
        # Validate init_id exists
        existing_cache = cache.get(request.init_id)
        if existing_cache is None:
            raise HTTPException(status_code=400, detail="Invalid init_id")
        
        # Generate page ID
        page_id = str(uuid.uuid4())
        
        # Update cache
        process_data = cache.get(request.init_id) or {}
        process_data[page_id] = {"status": "PENDING", "url": None}
        cache.set(request.init_id, process_data, expire=3600)
        
        # Start background task
        background_tasks.add_task(
            process_image_background,
            request.init_id,
            page_id,
            request.source_url,
            request.target_url,
            request.prompt
        )
        
        logger.info(f"Processing started: {request.init_id}, page: {page_id}")
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
    try:
        process_data = cache.get(request.process_id)
        if process_data is None:
            raise HTTPException(status_code=404, detail="Process not found")
        
        if request.page_id:
            if request.page_id not in process_data:
                raise HTTPException(status_code=404, detail="Page not found")
            page_data = process_data[request.page_id]
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
                status = page_data.get("status", "UNKNOWN")
                url = page_data.get("url")
                statuses.append(ProcessStatus(
                    process_id=request.process_id,
                    page_id=page_id,
                    status=status,
                    url=url
                ))
        
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