import os
from typing import Optional
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import io

class DocumentProcessor:
    @staticmethod
    async def process_pdf(file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"Error processing PDF: {str(e)}"

    @staticmethod
    async def process_image(file_path: str) -> str:
        """Extract text from image using OCR."""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            return f"Error processing image: {str(e)}"

    @staticmethod
    async def process_document(file_path: str, file_type: str) -> Optional[str]:
        """Process document based on its type."""
        if file_type == "pdf":
            return await DocumentProcessor.process_pdf(file_path)
        elif file_type in ["jpg", "jpeg", "png"]:
            return await DocumentProcessor.process_image(file_path)
        return None 