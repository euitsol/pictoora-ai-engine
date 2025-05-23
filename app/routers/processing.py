from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models.schemas import BookDetails, ProcessResponse
from app.services.processing_service import processing_service

router = APIRouter(prefix="/process", tags=["processing"])

@router.post("/book", response_model=ProcessResponse)
async def process_book(
    book_details: BookDetails,
    image_url: str,
    background_tasks: BackgroundTasks
):
    return await processing_service.start_processing(
        book_details.dict(),
        image_url,
        background_tasks
    )

@router.get("/status/{process_id}", response_model=ProcessResponse)
async def get_process_status(process_id: str):
    status = await processing_service.get_process_status(process_id)
    if not status:
        raise HTTPException(status_code=404, detail="Process not found")
    return status