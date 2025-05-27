import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import re
import pandas as pd
import fitz  # PyMuPDF
import os

class DataCollector:
    def __init__(self):
        # Use Homebrew's Tesseract path on macOS
        tesseract_path = '/opt/homebrew/bin/tesseract'
        if not os.path.exists(tesseract_path):
            tesseract_path = '/usr/local/bin/tesseract'  # Fallback path
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.arabic_config = r'--oem 3 --psm 6 -l ara+eng'
        self.english_config = r'--oem 3 --psm 6 -l eng'

    async def process_document(self, file_bytes: bytes, filename: str) -> dict:
        try:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                return self._process_image(file_bytes)
            elif filename.lower().endswith('.pdf'):
                return await self._process_pdf(file_bytes)
            else:
                raise ValueError("Unsupported file format")
        except Exception as e:
            print(f"Processing error: {str(e)}")
            return {}

    def _process_image(self, image_bytes: bytes) -> dict:
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, config=self._get_language_config(image))
        return self._extract_fields(text)

    async def _process_pdf(self, pdf_bytes: bytes) -> dict:
        # Check if PDF is text-based
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            if len(text) > 50:  # Has sufficient text
                return self._extract_fields(text)
        except:
            pass

        # Fallback to OCR for image-based PDF
        images = convert_from_bytes(pdf_bytes)
        combined_text = ""
        for image in images:
            combined_text += pytesseract.image_to_string(image, config=self.english_config)
        return self._extract_fields(combined_text)

    def _get_language_config(self, image: Image) -> str:
        # Simple language detection
        try:
            text = pytesseract.image_to_string(image, config=self.english_config)
            if re.search(r'[\u0600-\u06FF]', text):  # Arabic Unicode range
                return self.arabic_config
        except:
            pass
        return self.english_config

    def _extract_fields(self, text: str) -> dict:
        return {
            'income': self._extract_income(text),
            'family_size': self._extract_family_size(text),
            'address': self._extract_address(text)
        }

    def _extract_income(self, text: str) -> float:
        # AED currency detection with Arabic/English support
        matches = re.findall(r'(?:ر.ع|AED|د.إ)\s*([\d,]+)', text)
        if matches:
            return max([float(m.replace(',', '')) for m in matches])
        return 0.0

    def _extract_family_size(self, text: str) -> int:
        # Arabic and English number detection
        patterns = [
            r'عدد أفراد الأسرة\D*(\d+)',
            r'family members\D*(\d+)',
            r'(\d+)\s*(?:individual|member)',
            r'family size\D*(\d+)',  # Added more patterns
            r'number of family members\D*(\d+)',
            r'(\d+)\s*(?:family|members)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return 0

    def _extract_address(self, text: str) -> str:
        # Simple address extraction - you might want to enhance this
        address_patterns = [
            r'Address:?\s*([^\n]+)',
            r'العنوان:?\s*([^\n]+)',
            r'Location:?\s*([^\n]+)',  # Added more patterns
            r'Residence:?\s*([^\n]+)',
            r'Home:?\s*([^\n]+)'
        ]
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "" 