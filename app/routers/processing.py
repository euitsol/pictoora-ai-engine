from fastapi import APIRouter, BackgroundTasks
from app.models.schemas import BookDetails, ProcessResponse
from app.services.processing_service import processing_service
from app.services.processing_service import ProcessValidator
from app.utils.exceptions import APIException

router = APIRouter(prefix="/process", tags=["processing"])

@router.post("/book", response_model=ProcessResponse)
async def process_book(
    book_details: BookDetails,
    image_url: str,
    background_tasks: BackgroundTasks
):
    try:
        ProcessValidator().validate(book_details.model_dump())
        return await processing_service.start_processing(
            book_details.model_dump(),
            image_url,
            background_tasks
        )
    except APIException as e:
        raise e

@router.get("/status/{process_id}", response_model=ProcessResponse)
async def get_process_status(process_id: str):
    try:
        status = await processing_service.get_process_status(process_id)
    except APIException as e:
        raise e
    if not status:
        raise APIException(
            status_code=404,
            error_type="not_found",
            message="Process not found",
            code=1004,
            details={"process_id": process_id}
        )
    return status