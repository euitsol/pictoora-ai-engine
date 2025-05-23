from fastapi import APIRouter, UploadFile, Depends
from app.services.image_service import ImageService

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/upload")
async def upload_image(file: UploadFile):
    image_url = await ImageService.save_image(file)
    return {"url": image_url}