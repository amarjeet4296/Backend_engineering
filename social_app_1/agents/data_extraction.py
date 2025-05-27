"""
Data Extraction Agent - Handles multimodal document processing 
and information extraction from various document types.
"""

import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import re
import os
import logging
import pandas as pd
import fitz  # PyMuPDF
import json
from typing import Dict, List, Tuple, Any, Union
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataExtractionAgent:
    """
    Enhanced data extraction agent that can process multiple document types
    and extract structured information using OCR and multimodal techniques.
    """
    
    def __init__(self):
        """
        Initialize the data extraction agent with necessary components and models.
        """
        # Configure Tesseract
        tesseract_path = '/opt/homebrew/bin/tesseract'
        if not os.path.exists(tesseract_path):
            tesseract_path = '/usr/local/bin/tesseract'  # Fallback path
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Configure OCR settings
        self.arabic_config = r'--oem 3 --psm 6 -l ara+eng'
        self.english_config = r'--oem 3 --psm 6 -l eng'
        
        logger.info("DataExtractionAgent initialized")

    async def process_document(self, file_bytes: bytes, filename: str) -> dict:
        """
        Process a document and extract relevant information.
        
        Args:
            file_bytes: Raw bytes of the uploaded document
            filename: Name of the uploaded file
            
        Returns:
            Dict containing extracted information
        """
        try:
            logger.info(f"Processing document: {filename}")
            
            # Process based on file type
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                result = await self._process_image(file_bytes)
            elif filename.lower().endswith('.pdf'):
                result = await self._process_pdf(file_bytes)
            elif filename.lower().endswith(('.xlsx', '.xls')):
                result = await self._process_excel(file_bytes)
            else:
                raise ValueError(f"Unsupported file format: {filename}")
            
            # Add filename to result
            result['filename'] = filename
            
            return result
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return {"filename": filename, "error": str(e)}

    async def _process_image(self, image_bytes: bytes) -> dict:
        """
        Process an image document using OCR.
        
        Args:
            image_bytes: Raw bytes of the image
            
        Returns:
            Dict containing extracted information
        """
        # Open image
        image = Image.open(io.BytIO(image_bytes))
        
        # Determine language and run OCR
        config = self._get_language_config(image)
        text = pytesseract.image_to_string(image, config=config)
        
        # Extract structured fields
        return self._extract_fields(text)

    async def _process_pdf(self, pdf_bytes: bytes) -> dict:
        """
        Process a PDF document using text extraction and/or OCR.
        
        Args:
            pdf_bytes: Raw bytes of the PDF
            
        Returns:
            Dict containing extracted information
        """
        # Try text-based extraction first
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            
            # Extract text from each page
            for page in doc:
                text += page.get_text()
            
            # If sufficient text is found, process it
            if len(text) > 50:
                return self._extract_fields(text)
        except Exception as e:
            logger.warning(f"Text-based extraction failed: {str(e)}")
        
        # Fallback to OCR for image-based PDF
        logger.info("Falling back to OCR for PDF processing")
        images = convert_from_bytes(pdf_bytes)
        combined_text = ""
        
        # Process each page as an image
        for image in images:
            config = self._get_language_config(image)
            combined_text += pytesseract.image_to_string(image, config=config)
        
        return self._extract_fields(combined_text)

    async def _process_excel(self, excel_bytes: bytes) -> dict:
        """
        Process an Excel file to extract tabular data.
        
        Args:
            excel_bytes: Raw bytes of the Excel file
            
        Returns:
            Dict containing extracted information
        """
        # Read Excel file
        df = pd.read_excel(io.BytesIO(excel_bytes))
        
        # Extract financial information
        income = 0.0
        assets = 0.0
        liabilities = 0.0
        
        # Look for income, assets, and liabilities columns
        for col in df.columns:
            col_lower = col.lower()
            if 'income' in col_lower:
                income = self._extract_numeric_sum(df[col])
            elif 'asset' in col_lower:
                assets = self._extract_numeric_sum(df[col])
            elif 'liabilit' in col_lower or 'debt' in col_lower:
                liabilities = self._extract_numeric_sum(df[col])
        
        return {
            "income": income,
            "assets": assets,
            "liabilities": liabilities,
            "family_size": self._extract_family_size_from_excel(df),
            "address": self._extract_address_from_excel(df),
        }

    def _get_language_config(self, image: Image) -> str:
        """
        Detect the primary language in an image.
        
        Args:
            image: PIL Image object
            
        Returns:
            Tesseract configuration string for the detected language
        """
        try:
            # Get sample text using English config
            sample_text = pytesseract.image_to_string(image, config=self.english_config)
            
            # Check for Arabic characters
            if re.search(r'[\u0600-\u06FF]', sample_text):
                return self.arabic_config
        except Exception as e:
            logger.warning(f"Language detection error: {str(e)}")
        
        # Default to English
        return self.english_config

    def _extract_fields(self, text: str) -> dict:
        """
        Extract structured fields from extracted text.
        
        Args:
            text: Extracted text from document
            
        Returns:
            Dict containing structured fields
        """
        return {
            "income": self._extract_income(text),
            "family_size": self._extract_family_size(text),
            "address": self._extract_address(text),
            "employment_status": self._extract_employment_status(text),
            "demographic_info": self._extract_demographic_info(text),
            "assets": self._extract_assets(text),
            "liabilities": self._extract_liabilities(text)
        }

    def _extract_income(self, text: str) -> float:
        """
        Extract income value from text.
        
        Args:
            text: Extracted text
            
        Returns:
            Extracted income value
        """
        # Currency patterns (AED, USD, etc.)
        currency_patterns = [
            r'(?:annual|monthly|yearly)\s*income\D*(\d[\d,\.]+)',
            r'(?:ر.ع|AED|د.إ|USD|$)\s*([\d,\.]+)',
            r'income(?:[:\s])*(?:AED|د.إ|Dhs)?\s*([\d,\.]+)',
            r'salary(?:[:\s])*(?:AED|د.إ|Dhs)?\s*([\d,\.]+)'
        ]
        
        for pattern in currency_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Convert all matches to float and take the maximum
                values = [float(re.sub(r'[^\d\.]', '', m)) for m in matches]
                return max(values) if values else 0.0
                
        return 0.0

    def _extract_family_size(self, text: str) -> int:
        """
        Extract family size from text.
        
        Args:
            text: Extracted text
            
        Returns:
            Extracted family size
        """
        patterns = [
            r'(?:عدد أفراد الأسرة|family size|family members|household size|dependents)\D*(\d+)',
            r'(\d+)\s*(?:individual|member|dependent|family|household)',
            r'number of (?:family members|dependents|people in household)\D*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
                
        return 0

    def _extract_address(self, text: str) -> str:
        """
        Extract address from text.
        
        Args:
            text: Extracted text
            
        Returns:
            Extracted address
        """
        address_patterns = [
            r'(?:address|location|residence|home|العنوان)[:\s]*([^\n,\.]{5,100})',
            r'(?:lives at|living at|residing at)[:\s]*([^\n,\.]{5,100})'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return ""

    def _extract_employment_status(self, text: str) -> str:
        """
        Extract employment status from text.
        
        Args:
            text: Extracted text
            
        Returns:
            Extracted employment status
        """
        employment_patterns = [
            r'(?:employment status|work status|job status)[:\s]*([^\n,\.]{3,50})',
            r'(?:employed|unemployed|retired|student|self-employed|business owner)',
            r'(?:occupation|profession|job)[:\s]*([^\n,\.]{3,50})'
        ]
        
        for pattern in employment_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip() if len(match.groups()) > 0 else match.group(0).strip()
                
        return "Unknown"

    def _extract_demographic_info(self, text: str) -> dict:
        """
        Extract demographic information from text.
        
        Args:
            text: Extracted text
            
        Returns:
            Dict containing demographic information
        """
        # Extract age
        age_match = re.search(r'(?:age|years old)[:\s]*(\d{1,3})', text, re.IGNORECASE)
        age = int(age_match.group(1)) if age_match else 0
        
        # Extract gender
        gender_match = re.search(r'(?:gender|sex)[:\s]*(male|female|m|f)', text, re.IGNORECASE)
        gender = gender_match.group(1).lower() if gender_match else ""
        if gender == "m":
            gender = "male"
        elif gender == "f":
            gender = "female"
        
        # Extract nationality
        nationality_match = re.search(r'(?:nationality|citizen)[:\s]*([a-zA-Z ]{3,50})', text, re.IGNORECASE)
        nationality = nationality_match.group(1).strip() if nationality_match else ""
        
        return {
            "age": age,
            "gender": gender,
            "nationality": nationality
        }

    def _extract_assets(self, text: str) -> float:
        """
        Extract total assets value from text.
        
        Args:
            text: Extracted text
            
        Returns:
            Extracted assets value
        """
        asset_patterns = [
            r'(?:total assets|assets value|property value)[:\s]*(?:AED|د.إ|Dhs)?\s*([\d,\.]+)',
            r'(?:assets|properties|investments|savings)[:\s]*(?:AED|د.إ|Dhs)?\s*([\d,\.]+)'
        ]
        
        for pattern in asset_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                values = [float(re.sub(r'[^\d\.]', '', m)) for m in matches]
                return max(values) if values else 0.0
                
        return 0.0

    def _extract_liabilities(self, text: str) -> float:
        """
        Extract total liabilities value from text.
        
        Args:
            text: Extracted text
            
        Returns:
            Extracted liabilities value
        """
        liability_patterns = [
            r'(?:total liabilities|total debt|loans|debts)[:\s]*(?:AED|د.إ|Dhs)?\s*([\d,\.]+)',
            r'(?:liabilities|debts|loans|mortgage|credit)[:\s]*(?:AED|د.إ|Dhs)?\s*([\d,\.]+)'
        ]
        
        for pattern in liability_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                values = [float(re.sub(r'[^\d\.]', '', m)) for m in matches]
                return max(values) if values else 0.0
                
        return 0.0

    def _extract_numeric_sum(self, series: pd.Series) -> float:
        """
        Extract the sum of numeric values from a pandas Series.
        
        Args:
            series: Pandas Series containing numeric values
            
        Returns:
            Sum of numeric values
        """
        try:
            # Convert to numeric, coerce errors to NaN
            numeric_series = pd.to_numeric(series, errors='coerce')
            # Sum non-NaN values
            return numeric_series.sum()
        except Exception as e:
            logger.warning(f"Error summing numeric values: {str(e)}")
            return 0.0

    def _extract_family_size_from_excel(self, df: pd.DataFrame) -> int:
        """
        Extract family size from Excel data.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            Extracted family size
        """
        # Look for family size in column names
        for col in df.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['family', 'household', 'dependent']):
                # Get non-NaN values
                values = df[col].dropna()
                if not values.empty:
                    # Try to get the first numeric value
                    try:
                        return int(pd.to_numeric(values.iloc[0], errors='coerce'))
                    except:
                        pass
        
        return 0

    def _extract_address_from_excel(self, df: pd.DataFrame) -> str:
        """
        Extract address from Excel data.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            Extracted address
        """
        # Look for address in column names
        for col in df.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['address', 'location', 'residence']):
                # Get non-NaN values
                values = df[col].dropna()
                if not values.empty:
                    # Get the first value as string
                    return str(values.iloc[0])
        
        return ""
