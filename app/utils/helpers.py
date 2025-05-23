import uuid
from fastapi import UploadFile
class Helper:
    @staticmethod
    def generate_book_id():
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_page_id():
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_user_id():
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_process_id():
        return str(uuid.uuid4())
    
    @staticmethod
    def file_name(file: UploadFile):
        file_ext = file.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        return file_name