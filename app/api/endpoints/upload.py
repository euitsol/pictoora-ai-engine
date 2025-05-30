from fastapi import APIRouter, UploadFile, File, HTTPException
from ...schemas.responses import UploadResponse, FileUploadResponse
from ...core.config import settings
from ...core.logger import get_logger
import os
import uuid
from typing import List
from pathlib import Path

logger = get_logger()
router = APIRouter()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to the storage/uploads directory
    """
    try:
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        new_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Use Path for proper path handling
        upload_path = Path("storage/uploads")
        file_path = upload_path / new_filename
        
        # Save the file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Generate file URL with API_V1_STR prefix
        file_url = f"{settings.APP_URL}/storage/uploads/{new_filename}"
        relative_path = str(Path("storage/uploads") / new_filename)
        
        logger.info(f"File uploaded successfully: {relative_path}")
        return UploadResponse(
            status_code=2000,
            message="File uploaded successfully",
            data=FileUploadResponse(
                file_path=relative_path.replace(os.sep, '/'),
                file_url=file_url
            )
        )
        
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        return UploadResponse(
            status_code=2001,
            message="File upload failed",
            error=str(e)
        ) 