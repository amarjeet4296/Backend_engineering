"""
Multimodal Processing Module - Handles processing of various document types
including text, images, and tabular data.
"""

import logging
import os
import io
import re
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
from pdf2image import convert_from_bytes

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultimodalProcessor:
    """
    Processor for handling multiple data modalities (text, images, tables) for
    social security application documents.
    """
    
    def __init__(self):
        """
        Initialize the multimodal processor with necessary components.
        """
        # Configure Tesseract for OCR
        tesseract_path = '/opt/homebrew/bin/tesseract'
        if not os.path.exists(tesseract_path):
            tesseract_path = '/usr/local/bin/tesseract'  # Fallback path
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # OCR configuration
        self.config_eng = r'--oem 3 --psm 6 -l eng'
        self.config_ara = r'--oem 3 --psm 6 -l ara+eng'
        
        logger.info("MultimodalProcessor initialized")

    def process_document(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Process a document based on its type.
        
        Args:
            file_bytes: Raw bytes of the document
            filename: Name of the file
            
        Returns:
            Dictionary with extracted information
        """
        try:
            # Determine file type from extension
            file_extension = os.path.splitext(filename)[1].lower()
            
            # Process based on file type
            if file_extension in ['.jpg', '.jpeg', '.png']:
                return self.process_image(file_bytes)
            elif file_extension == '.pdf':
                return self.process_pdf(file_bytes)
            elif file_extension in ['.xlsx', '.xls']:
                return self.process_excel(file_bytes)
            elif file_extension in ['.csv']:
                return self.process_csv(file_bytes)
            elif file_extension in ['.txt', '.json', '.xml']:
                return self.process_text(file_bytes, file_extension)
            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                return {"error": f"Unsupported file type: {file_extension}"}
        
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return {"error": f"Processing error: {str(e)}"}

    def process_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Process an image document using OCR.
        
        Args:
            image_bytes: Raw bytes of the image
            
        Returns:
            Dictionary with extracted information
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Detect language and apply OCR
            config = self._detect_language(image)
            text = pytesseract.image_to_string(image, config=config)
            
            # Extract structured information
            return self._extract_structured_data(text)
        
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {"error": f"Image processing error: {str(e)}"}

    def process_pdf(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Process a PDF document.
        
        Args:
            pdf_bytes: Raw bytes of the PDF
            
        Returns:
            Dictionary with extracted information
        """
        try:
            # Try to extract text directly first
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            extracted_text = ""
            
            # Check for text content
            for page in doc:
                page_text = page.get_text()
                extracted_text += page_text
            
            # If sufficient text was extracted, process it
            if len(extracted_text) > 100:
                logger.info("Successfully extracted text from PDF")
                structured_data = self._extract_structured_data(extracted_text)
                return structured_data
            
            # If not enough text, use OCR
            logger.info("Not enough text found in PDF, using OCR")
            return self._process_pdf_with_ocr(pdf_bytes)
        
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return {"error": f"PDF processing error: {str(e)}"}

    def _process_pdf_with_ocr(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Process a PDF document using OCR.
        
        Args:
            pdf_bytes: Raw bytes of the PDF
            
        Returns:
            Dictionary with extracted information
        """
        try:
            # Convert PDF to images
            images = convert_from_bytes(pdf_bytes)
            
            # Process each page with OCR
            full_text = ""
            for img in images:
                config = self._detect_language(img)
                page_text = pytesseract.image_to_string(img, config=config)
                full_text += page_text + "\n\n"
            
            # Extract structured information
            return self._extract_structured_data(full_text)
        
        except Exception as e:
            logger.error(f"Error processing PDF with OCR: {str(e)}")
            return {"error": f"PDF OCR error: {str(e)}"}

    def process_excel(self, excel_bytes: bytes) -> Dict[str, Any]:
        """
        Process an Excel document.
        
        Args:
            excel_bytes: Raw bytes of the Excel file
            
        Returns:
            Dictionary with extracted information
        """
        try:
            # Load Excel file
            df = pd.read_excel(io.BytesIO(excel_bytes))
            
            # Extract financial information
            result = {}
            
            # Look for income data
            for col in df.columns:
                col_lower = col.lower()
                if 'income' in col_lower or 'salary' in col_lower or 'earning' in col_lower:
                    income_values = pd.to_numeric(df[col], errors='coerce')
                    result['income'] = float(income_values.max()) if not income_values.empty else 0.0
            
            # Look for assets data
            for col in df.columns:
                col_lower = col.lower()
                if 'asset' in col_lower or 'property' in col_lower or 'investment' in col_lower:
                    asset_values = pd.to_numeric(df[col], errors='coerce')
                    result['assets'] = float(asset_values.sum()) if not asset_values.empty else 0.0
            
            # Look for liabilities data
            for col in df.columns:
                col_lower = col.lower()
                if 'liab' in col_lower or 'debt' in col_lower or 'loan' in col_lower:
                    liability_values = pd.to_numeric(df[col], errors='coerce')
                    result['liabilities'] = float(liability_values.sum()) if not liability_values.empty else 0.0
            
            # Look for family size
            for col in df.columns:
                col_lower = col.lower()
                if 'family' in col_lower or 'household' in col_lower or 'dependents' in col_lower:
                    family_values = pd.to_numeric(df[col], errors='coerce')
                    if not family_values.empty and not family_values.isna().all():
                        result['family_size'] = int(family_values.iloc[0])
            
            # Convert DataFrame to structured tables for further analysis
            tables = {}
            for i, sheet_name in enumerate(pd.ExcelFile(io.BytesIO(excel_bytes)).sheet_names):
                sheet_df = pd.read_excel(io.BytesIO(excel_bytes), sheet_name=sheet_name)
                tables[f"table_{i+1}"] = sheet_df.to_dict(orient='records')
            
            result['tables'] = tables
            return result
        
        except Exception as e:
            logger.error(f"Error processing Excel: {str(e)}")
            return {"error": f"Excel processing error: {str(e)}"}

    def process_csv(self, csv_bytes: bytes) -> Dict[str, Any]:
        """
        Process a CSV document.
        
        Args:
            csv_bytes: Raw bytes of the CSV file
            
        Returns:
            Dictionary with extracted information
        """
        try:
            # Load CSV file
            df = pd.read_csv(io.BytesIO(csv_bytes))
            
            # Similar processing as Excel
            result = {}
            
            # Look for income data
            for col in df.columns:
                col_lower = col.lower()
                if 'income' in col_lower or 'salary' in col_lower:
                    income_values = pd.to_numeric(df[col], errors='coerce')
                    result['income'] = float(income_values.max()) if not income_values.empty else 0.0
            
            # Look for assets and liabilities
            for col in df.columns:
                col_lower = col.lower()
                if 'asset' in col_lower:
                    asset_values = pd.to_numeric(df[col], errors='coerce')
                    result['assets'] = float(asset_values.sum()) if not asset_values.empty else 0.0
                elif 'liab' in col_lower or 'debt' in col_lower:
                    liability_values = pd.to_numeric(df[col], errors='coerce')
                    result['liabilities'] = float(liability_values.sum()) if not liability_values.empty else 0.0
            
            # Store table data
            result['table'] = df.to_dict(orient='records')
            return result
        
        except Exception as e:
            logger.error(f"Error processing CSV: {str(e)}")
            return {"error": f"CSV processing error: {str(e)}"}

    def process_text(self, text_bytes: bytes, file_extension: str) -> Dict[str, Any]:
        """
        Process a text document.
        
        Args:
            text_bytes: Raw bytes of the text file
            file_extension: File extension to determine processing method
            
        Returns:
            Dictionary with extracted information
        """
        try:
            # Convert bytes to string
            text = text_bytes.decode('utf-8')
            
            # Process based on file type
            if file_extension == '.json':
                # Parse JSON
                data = json.loads(text)
                return data
            else:
                # Regular text processing
                return self._extract_structured_data(text)
        
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            return {"error": f"Text processing error: {str(e)}"}

    def _detect_language(self, image: Image) -> str:
        """
        Detect language in an image for OCR configuration.
        
        Args:
            image: PIL Image object
            
        Returns:
            OCR configuration string
        """
        try:
            # Get sample text with English config
            sample_text = pytesseract.image_to_string(image, config=self.config_eng)
            
            # Check for Arabic characters
            if re.search(r'[\u0600-\u06FF]', sample_text):
                return self.config_ara
            
            return self.config_eng
        
        except Exception as e:
            logger.warning(f"Language detection error: {str(e)}")
            return self.config_eng  # Default to English

    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """
        Extract structured data from text.
        
        Args:
            text: Extracted text content
            
        Returns:
            Dictionary with structured data
        """
        result = {}
        
        # Extract income
        income_patterns = [
            r'(?:income|salary|earnings)[:\s]*(?:AED|د.إ|Dhs)?\s*([\d,\.]+)',
            r'(?:AED|د.إ|Dhs|USD|\$)\s*([\d,\.]+)(?:[^\d]+(?:income|salary|earnings))',
            r'(?:annual|monthly|yearly)[^\d]+([\d,\.]+)(?:[^\d]+(?:income|salary))?'
        ]
        
        for pattern in income_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                values = [float(re.sub(r'[^\d\.]', '', m)) for m in matches]
                result['income'] = max(values)
                break
        
        # Extract family size
        family_patterns = [
            r'(?:family size|family members|household size|dependents)[:\s]*(\d+)',
            r'(\d+)\s*(?:family members|members in household|dependents)',
            r'(?:number of|no\.)[^\d]+(?:family|household|dependents)[^\d]+(\d+)'
        ]
        
        for pattern in family_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    result['family_size'] = int(match.group(1))
                    break
                except ValueError:
                    pass
        
        # Extract address
        address_patterns = [
            r'(?:address|location|residence)[:\s]*([^\n]{10,100})',
            r'(?:lives at|residing at)[:\s]*([^\n]{10,100})'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['address'] = match.group(1).strip()
                break
        
        # Extract employment status
        employment_patterns = [
            r'(?:employment|job)[^\d:]*(?:status)?[:\s]*([^\n]{3,50})',
            r'(?:employed|unemployed|retired|student|self-employed)',
            r'(?:profession|occupation)[:\s]*([^\n]{3,50})'
        ]
        
        for pattern in employment_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['employment_status'] = match.group(0).strip() if len(match.groups()) == 0 else match.group(1).strip()
                break
        
        # Extract assets
        asset_patterns = [
            r'(?:assets|properties|investments)[:\s]*(?:AED|د.إ|Dhs)?\s*([\d,\.]+)',
            r'(?:total assets|net worth)[:\s]*(?:AED|د.إ|Dhs)?\s*([\d,\.]+)'
        ]
        
        for pattern in asset_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                values = [float(re.sub(r'[^\d\.]', '', m)) for m in matches]
                result['assets'] = max(values)
                break
        
        # Extract liabilities
        liability_patterns = [
            r'(?:liabilities|debts|loans)[:\s]*(?:AED|د.إ|Dhs)?\s*([\d,\.]+)',
            r'(?:total debt|outstanding loans)[:\s]*(?:AED|د.إ|Dhs)?\s*([\d,\.]+)'
        ]
        
        for pattern in liability_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                values = [float(re.sub(r'[^\d\.]', '', m)) for m in matches]
                result['liabilities'] = max(values)
                break
        
        # Extract demographic information
        age_match = re.search(r'(?:age|years old)[:\s]*(\d{1,3})', text, re.IGNORECASE)
        if age_match:
            result['age'] = int(age_match.group(1))
        
        gender_match = re.search(r'(?:gender|sex)[:\s]*(male|female|m|f)', text, re.IGNORECASE)
        if gender_match:
            gender = gender_match.group(1).lower()
            result['gender'] = 'male' if gender in ['m', 'male'] else 'female'
        
        nationality_match = re.search(r'(?:nationality|citizen)[:\s]*([a-zA-Z ]{3,50})', text, re.IGNORECASE)
        if nationality_match:
            result['nationality'] = nationality_match.group(1).strip()
        
        return result

    def extract_entities_from_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract structured entities from an image using OCR.
        
        Args:
            image_bytes: Raw bytes of the image
            
        Returns:
            Dictionary with extracted entities
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Detect language and apply OCR
            config = self._detect_language(image)
            text = pytesseract.image_to_string(image, config=config)
            
            # Extract structured information
            return self._extract_structured_data(text)
        
        except Exception as e:
            logger.error(f"Error extracting entities from image: {str(e)}")
            return {"error": f"Entity extraction error: {str(e)}"}

    def merge_document_data(self, document_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge data from multiple documents into a single consolidated record.
        
        Args:
            document_data_list: List of dictionaries with extracted data
            
        Returns:
            Consolidated dictionary with merged data
        """
        if not document_data_list:
            return {}
        
        # Initialize result with first document
        result = document_data_list[0].copy()
        
        # Define numeric fields to merge
        numeric_fields = ['income', 'family_size', 'assets', 'liabilities', 'age']
        
        # Define text fields to merge
        text_fields = ['address', 'employment_status', 'gender', 'nationality']
        
        # Process each additional document
        for doc_data in document_data_list[1:]:
            # Skip documents with errors
            if 'error' in doc_data:
                continue
            
            # Merge numeric fields (take max for income, assets; min for liabilities)
            for field in numeric_fields:
                if field in doc_data:
                    if field not in result:
                        result[field] = doc_data[field]
                    elif field in ['income', 'assets']:
                        result[field] = max(result[field], doc_data[field])
                    elif field == 'liabilities':
                        result[field] = min(result[field], doc_data[field])
                    elif field == 'family_size':
                        # For family size, prefer non-zero values
                        if result[field] == 0 and doc_data[field] > 0:
                            result[field] = doc_data[field]
                        elif doc_data[field] > 0:
                            # Take average and round to nearest integer
                            result[field] = round((result[field] + doc_data[field]) / 2)
            
            # Merge text fields (prefer non-empty values)
            for field in text_fields:
                if field in doc_data and doc_data[field]:
                    if field not in result or not result[field]:
                        result[field] = doc_data[field]
            
            # Merge tables if present
            if 'tables' in doc_data:
                if 'tables' not in result:
                    result['tables'] = {}
                result['tables'].update(doc_data['tables'])
        
        return result
