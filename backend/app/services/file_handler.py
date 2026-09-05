import os
import uuid
import logging
from typing import Tuple, Optional
from fastapi import UploadFile
import PyPDF2
from io import BytesIO

log = logging.getLogger("uvicorn.error")

class FileHandler:
    UPLOAD_DIR = "uploads"
    
    @classmethod
    async def save_file(cls, file: UploadFile, anon_id: str, application_id: int) -> str:
        """Save an uploaded file to the uploads directory"""
        # Create directory: uploads/{anon_id}/{application_id}/
        path = os.path.join(cls.UPLOAD_DIR, anon_id, str(application_id))
        os.makedirs(path, exist_ok=True)
        
        file_path = os.path.join(path, file.filename)
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
            
        await file.seek(0) # Reset file pointer for future reads
        return os.path.abspath(file_path)

    @classmethod
    async def extract_text_from_pdf(cls, file_content: bytes) -> str:
        """Extract text from a PDF file content"""
        try:
            reader = PyPDF2.PdfReader(BytesIO(file_content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            log.error(f"Failed to extract text from PDF: {str(e)}")
            raise ValueError(f"Invalid PDF file: {str(e)}")

    @classmethod
    async def process_resume(cls, file: UploadFile, anon_id: str, application_id: int) -> Tuple[str, str, str]:
        """Process a resume PDF: save it and extract text"""
        if not file.filename.endswith('.pdf'):
            raise ValueError("Only PDF resumes are supported")
            
        # Save file
        file_path = await cls.save_file(file, anon_id, application_id)
        
        # Extract text
        content = await file.read()
        text = await cls.extract_text_from_pdf(content)
        
        # Calculate a simple hash for verification (placeholder)
        resume_hash = str(uuid.uuid4())
        
        return file_path, resume_hash, text

    @classmethod
    async def process_linkedin_pdf(cls, file: UploadFile, anon_id: str, application_id: int) -> Optional[Tuple[str, str]]:
        """Process a LinkedIn profile PDF"""
        if not file or not file.filename:
            return None
            
        if not file.filename.endswith('.pdf'):
            log.warning("LinkedIn file is not a PDF, skipping")
            return None
            
        # Save file
        file_path = await cls.save_file(file, anon_id, application_id)
        
        # Extract text
        content = await file.read()
        text = await cls.extract_text_from_pdf(content)
        
        return file_path, text
