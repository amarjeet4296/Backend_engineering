"""
Data Validation Agent - Advanced validation of extracted data with reasoning capabilities.
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional
from langchain_community.llms import Ollama
from utils.reasoning import ReActReasoning

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataValidationAgent:
    """
    Enhanced data validation agent with advanced validation capabilities
    and reasoning for inconsistency detection.
    """
    
    def __init__(self, model_name: str = "mistral"):
        """
        Initialize the data validation agent with validation rules and reasoning.
        
        Args:
            model_name: Name of the local LLM model to use
        """
        self.model_name = model_name
        
        # Set up basic validation rules
        self.validation_rules = {
            "income": self._validate_income,
            "family_size": self._validate_family_size,
            "address": self._validate_address,
            "filename": self._validate_filename,
            "employment_status": self._validate_employment_status,
            "assets": self._validate_assets,
            "liabilities": self._validate_liabilities
        }
        
        # Initialize reasoning for complex validations
        self.reasoning = ReActReasoning(model_name=model_name)
        
        logger.info("DataValidationAgent initialized")

    def validate(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate the extracted data against defined rules and check for inconsistencies.
        
        Args:
            data: Dictionary of extracted data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        required_fields = ["income", "family_size", "address", "filename"]
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Apply basic validation rules to each field
        for field, rule in self.validation_rules.items():
            if field in data:
                value = data[field]
                if not rule(value):
                    errors.append(self._get_error_message(field, value))
        
        # Perform cross-field validations for consistency
        if not missing_fields:
            consistency_errors = self._validate_consistency(data)
            errors.extend(consistency_errors)
        
        is_valid = len(errors) == 0
        logger.info(f"Validation result: {'valid' if is_valid else 'invalid'}")
        
        return is_valid, errors

    def _validate_income(self, value: Any) -> bool:
        """
        Validate income value.
        
        Args:
            value: Income value to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not isinstance(value, (int, float)):
                return False
            return 0 <= value <= 1_000_000  # Reasonable upper limit for AED
        except Exception:
            return False

    def _validate_family_size(self, value: Any) -> bool:
        """
        Validate family size.
        
        Args:
            value: Family size value to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not isinstance(value, int):
                return False
            return 1 <= value <= 20  # Reasonable range
        except Exception:
            return False

    def _validate_address(self, value: Any) -> bool:
        """
        Validate address.
        
        Args:
            value: Address value to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not isinstance(value, str):
                return False
            return 5 <= len(value.strip()) <= 200  # Reasonable length
        except Exception:
            return False

    def _validate_filename(self, value: Any) -> bool:
        """
        Validate filename.
        
        Args:
            value: Filename value to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not isinstance(value, str):
                return False
            valid_extensions = ('.pdf', '.png', '.jpg', '.jpeg', '.xlsx', '.xls')
            return value.lower().endswith(valid_extensions)
        except Exception:
            return False

    def _validate_employment_status(self, value: Any) -> bool:
        """
        Validate employment status.
        
        Args:
            value: Employment status value to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not value:
            return True  # Optional field
            
        try:
            if not isinstance(value, str):
                return False
                
            valid_statuses = [
                'employed', 'unemployed', 'self-employed', 'retired', 
                'student', 'business owner', 'contractor', 'freelancer'
            ]
            
            # Check if value is or contains a valid status
            value_lower = value.lower()
            return any(status in value_lower for status in valid_statuses) and len(value) <= 100
        except Exception:
            return False

    def _validate_assets(self, value: Any) -> bool:
        """
        Validate assets value.
        
        Args:
            value: Assets value to validate
            
        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return True  # Optional field
            
        try:
            if not isinstance(value, (int, float)):
                return False
            return 0 <= value <= 100_000_000  # Reasonable upper limit for AED
        except Exception:
            return False

    def _validate_liabilities(self, value: Any) -> bool:
        """
        Validate liabilities value.
        
        Args:
            value: Liabilities value to validate
            
        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return True  # Optional field
            
        try:
            if not isinstance(value, (int, float)):
                return False
            return 0 <= value <= 10_000_000  # Reasonable upper limit for AED
        except Exception:
            return False

    def _validate_consistency(self, data: Dict) -> List[str]:
        """
        Validate consistency across multiple fields.
        
        Args:
            data: Dictionary of extracted data
            
        Returns:
            List of consistency error messages
        """
        consistency_errors = []
        
        # Income should be reasonable relative to assets and liabilities
        if all(key in data for key in ['income', 'assets', 'liabilities']):
            income = data['income']
            assets = data['assets']
            liabilities = data['liabilities']
            
            # If liabilities are more than 10x income, flag it
            if income > 0 and liabilities > income * 10:
                consistency_errors.append(
                    f"Potential inconsistency: Liabilities ({liabilities} AED) are more than 10x "
                    f"annual income ({income} AED)"
                )
            
            # If assets are more than 50x income without explanation, flag it
            if income > 0 and assets > income * 50:
                consistency_errors.append(
                    f"Potential inconsistency: Assets ({assets} AED) are more than 50x "
                    f"annual income ({income} AED)"
                )
        
        # Income per family member reasonability check
        if all(key in data for key in ['income', 'family_size']) and data['family_size'] > 0:
            income_per_member = data['income'] / data['family_size']
            
            # If income per member is extremely low, flag it
            if income_per_member < 1000:  # Less than 1000 AED per family member per year
                consistency_errors.append(
                    f"Potential inconsistency: Income per family member ({income_per_member:.2f} AED) "
                    f"is unrealistically low"
                )
        
        # Use reasoning to detect other inconsistencies
        if len(data) >= 3:  # Only if we have enough data
            try:
                llm_consistency_errors = self._detect_inconsistencies_with_reasoning(data)
                consistency_errors.extend(llm_consistency_errors)
            except Exception as e:
                logger.warning(f"Error in consistency reasoning: {str(e)}")
        
        return consistency_errors

    def _detect_inconsistencies_with_reasoning(self, data: Dict) -> List[str]:
        """
        Use LLM reasoning to detect potential inconsistencies in the data.
        
        Args:
            data: Dictionary of extracted data
            
        Returns:
            List of potential inconsistency messages
        """
        # Prepare input for the reasoning model
        prompt = f"""
        Analyze the following applicant data for a social security application and identify any inconsistencies:
        
        Income: {data.get('income', 'Not provided')} AED
        Family Size: {data.get('family_size', 'Not provided')}
        Address: {data.get('address', 'Not provided')}
        Employment Status: {data.get('employment_status', 'Not provided')}
        Assets: {data.get('assets', 'Not provided')} AED
        Liabilities: {data.get('liabilities', 'Not provided')} AED
        
        Identify only clear inconsistencies in the data, such as:
        1. Conflicts between income and employment status
        2. Unrealistic relationships between values
        3. Logical contradictions
        
        For each inconsistency, provide a brief explanation. If there are no clear inconsistencies, return an empty list.
        """
        
        # Get reasoning analysis
        try:
            llm = Ollama(model=self.model_name)
            response = llm.invoke(prompt)
            
            # Extract inconsistencies from response
            inconsistencies = []
            for line in response.split('\n'):
                line = line.strip()
                if line and len(line) > 10 and ('inconsistency' in line.lower() or 'conflict' in line.lower()):
                    inconsistencies.append(line)
            
            return inconsistencies
        except Exception as e:
            logger.error(f"LLM reasoning error: {str(e)}")
            return []

    def _get_error_message(self, field: str, value: Any) -> str:
        """
        Generate a descriptive error message for a failed validation.
        
        Args:
            field: Name of the field that failed validation
            value: Value that failed validation
            
        Returns:
            Error message string
        """
        error_messages = {
            "income": f"Invalid income value: {value}. Must be a number between 0 and 1,000,000 AED.",
            "family_size": f"Invalid family size: {value}. Must be a number between 1 and 20.",
            "address": f"Invalid address: '{value}'. Must be between 5 and 200 characters.",
            "filename": f"Invalid filename: '{value}'. Must end with .pdf, .png, .jpg, .jpeg, .xlsx, or .xls.",
            "employment_status": f"Invalid employment status: '{value}'. Must be a recognized status (employed, unemployed, etc.).",
            "assets": f"Invalid assets value: {value}. Must be a number between 0 and 100,000,000 AED.",
            "liabilities": f"Invalid liabilities value: {value}. Must be a number between 0 and 10,000,000 AED."
        }
        
        return error_messages.get(field, f"Validation failed for '{field}': {value}")
