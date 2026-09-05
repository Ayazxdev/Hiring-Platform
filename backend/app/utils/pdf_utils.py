
import os
import pypdf
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file path using pypdf.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
    """
    try:
        text = ""
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # 2026 Fix: Ensure valid UTF-8 and remove unprintable chars that crash Windows console
        if text:
            text = text.encode('utf-8', errors='ignore').decode('utf-8')

        return text.strip()
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {str(e)}")
        return ""

def save_upload_file(upload_file, dest_folder: str, filename: str) -> Optional[str]:
    """
    Save an uploaded file to a destination folder.
    
    Args:
        upload_file: FastAPI UploadFile object
        dest_folder: Destination folder path
        filename: Target filename
        
    Returns:
        Absolute path to the saved file, or None if failed
    """
    try:
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
            
        file_path = os.path.join(dest_folder, filename)
        
        # Save file chunks to handle large files efficiently
        with open(file_path, "wb") as f:
            while content := upload_file.file.read(1024 * 1024):  # 1MB chunks
                f.write(content)
                
        # Reset file pointer for subsequent operations
        upload_file.file.seek(0)
            
        return os.path.abspath(file_path)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {str(e)}")
        return None
