import os
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.document_template import DocumentTemplate
from app.config import get_settings

settings = get_settings()


class TemplateService:
    @staticmethod
    def save_template_file(file_bytes: bytes, file_name: str) -> str:
        """Save template file and return file path."""
        template_dir = os.path.join(settings.storage_dir, "templates")
        os.makedirs(template_dir, exist_ok=True)
        
        file_path = os.path.join(template_dir, file_name)
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        
        return file_path
    
    @staticmethod
    def delete_template_file(file_path: str) -> None:
        """Delete template file."""
        if os.path.exists(file_path):
            os.remove(file_path)
