class ValidatorAgent:
    def __init__(self):
        """
        Initializes the validator with rules specific to our document data.
        """
        self.validation_rules = {
            "income": self._validate_income,
            "family_size": self._validate_family_size,
            "address": self._validate_address,
            "filename": self._validate_filename
        }

    def _validate_income(self, value):
        """
        Validates income value.
        Rules:
        - Must be a number (int or float)
        - Must be non-negative
        - Must be less than 1 million AED (reasonable upper limit)
        """
        try:
            if not isinstance(value, (int, float)):
                return False
            return 0 <= value <= 1_000_000
        except:
            return False

    def _validate_family_size(self, value):
        """
        Validates family size.
        Rules:
        - Must be an integer
        - Must be between 1 and 20 (reasonable range)
        """
        try:
            if not isinstance(value, int):
                return False
            return 1 <= value <= 20
        except:
            return False

    def _validate_address(self, value):
        """
        Validates address.
        Rules:
        - Must be a string
        - Must not be empty
        - Must be at least 5 characters long
        - Must not exceed 200 characters
        """
        try:
            if not isinstance(value, str):
                return False
            return 5 <= len(value.strip()) <= 200
        except:
            return False

    def _validate_filename(self, value):
        """
        Validates filename.
        Rules:
        - Must be a string
        - Must not be empty
        - Must have a valid extension (.pdf, .png, .jpg, .jpeg)
        """
        try:
            if not isinstance(value, str):
                return False
            valid_extensions = ('.pdf', '.png', '.jpg', '.jpeg')
            return value.lower().endswith(valid_extensions)
        except:
            return False

    def validate(self, data):
        """
        Validate incoming data against the defined rules.
        :param data: Dict representing data from DataCollector
        :return: Tuple (is_valid: bool, errors: list)
        """
        errors = []
        
        # Check if all required fields are present
        required_fields = ["income", "family_size", "address", "filename"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Validate each field that is present
        for field, rule in self.validation_rules.items():
            if field in data:
                value = data[field]
                if not rule(value):
                    errors.append(self._get_error_message(field, value))
        
        is_valid = len(errors) == 0
        return is_valid, errors

    def _get_error_message(self, field, value):
        """
        Generate a descriptive error message for a failed validation.
        """
        error_messages = {
            "income": f"Invalid income value: {value}. Must be a number between 0 and 1,000,000 AED.",
            "family_size": f"Invalid family size: {value}. Must be a number between 1 and 20.",
            "address": f"Invalid address: '{value}'. Must be between 5 and 200 characters.",
            "filename": f"Invalid filename: '{value}'. Must end with .pdf, .png, .jpg, or .jpeg."
        }
        return error_messages.get(field, f"Validation failed for '{field}': {value}") 