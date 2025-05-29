from fastapi import APIRouter, BackgroundTasks
from app.models.schemas import BookDetails, ProcessResponse
from app.services.processing_service import processing_service
from app.utils.exceptions import APIException

router = APIRouter(prefix="/process", tags=["processing"])

@router.post("/book", response_model=ProcessResponse)
async def process_book(
    book_details: BookDetails,
    background_tasks: BackgroundTasks
):
    """
    Start processing a book with face-swapping for each page.
    Returns a process ID that can be used to check the status.
    """
    try:
        response = await processing_service.start_processing(
            book_details.model_dump(),
            background_tasks
        )
        return response
    except APIException as e:
        raise e
    except Exception as e:
        raise APIException(
            status_code=500,
            error_type="processing_error",
            message="Failed to start processing",
            details={"error": str(e)}
        )

@router.get("/status/{process_id}", response_model=ProcessResponse)
async def get_process_status(process_id: str):
    """
    Get the status of a processing job.
    Returns the current status and output URL if processing is complete.
    """
    try:
        status = await processing_service.get_process_status(process_id)
        if not status:
            raise APIException(
                status_code=404,
                error_type="not_found",
                message="Process not found",
                code=1004,
                details={"process_id": process_id}
            )
        return status
    except APIException as e:
        raise e
    except Exception as e:
        raise APIException(
            status_code=500,
            error_type="server_error",
            message="Failed to get process status",
            details={"error": str(e)}
        )