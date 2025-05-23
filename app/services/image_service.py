import imghdr
from fastapi import UploadFile, HTTPException
from app.utils.exceptions import APIException
from app.config.settings import settings
from app.utils.helpers import Helper
import os

class ImageValidator:
    ALLOWED_FORMATS = ["jpeg", "png", "jpg"]
    MAX_FILE_SIZE = 10 * 1024 * 1024

    @classmethod
    async def validate(cls, file: UploadFile):
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > cls.MAX_FILE_SIZE:
            raise APIException(
                status_code=422,
                error_type="validation_error",
                message=f"File size exceeds maximum allowed size of {cls.MAX_FILE_SIZE} bytes",
                code=1001,
                details={"max_size": cls.MAX_FILE_SIZE, "actual_size": file_size}
            )

        file_format = imghdr.what(file.file)
        if file_format not in cls.ALLOWED_FORMATS:
            raise APIException(
                status_code=422,
                error_type="validation_error",
                message="Invalid file format",
                code=1002,
                details={"allowed_formats": cls.ALLOWED_FORMATS}
            )

        await file.seek(0)

class ImageService:
    @staticmethod
    async def save_image(file: UploadFile) -> str:
        try:
            await ImageValidator.validate(file)
            
            file_name = Helper.file_name(file)
            file_path = os.path.join(settings.STORAGE_PATH, file_name)
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            return f"{settings.BASE_URL}/{settings.STORAGE_PATH}/{file_name}"
            
        except APIException as e:
            raise e
        except Exception as e:
            raise APIException(
                status_code=500,
                error_type="server_error",
                message="An error occurred while processing the image",
                code=1003,
                details={"error": str(e)}
            )