"""
Synthetic Data Generator - Creates realistic synthetic data for testing and
training machine learning models for the social security application system.
"""

import logging
import json
import os
import random
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyntheticDataGenerator:
    """
    Generates synthetic data for testing and training machine learning models
    in the social security application system.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the synthetic data generator.
        
        Args:
            seed: Optional random seed for reproducibility
        """
        # Set random seed if provided
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # Define data distributions and parameters
        self.income_params = {
            'low': (30000, 10000),    # mean, std for low income
            'medium': (60000, 15000), # mean, std for medium income
            'high': (120000, 30000)   # mean, std for high income
        }
        
        self.employment_statuses = [
            'Employed', 'Self-employed', 'Unemployed', 'Retired', 
            'Student', 'Part-time', 'Contract', 'Business Owner'
        ]
        
        self.nationalities = [
            'UAE', 'India', 'Pakistan', 'Egypt', 'Philippines', 
            'Jordan', 'Lebanon', 'Syria', 'UK', 'USA'
        ]
        
        self.emirates = [
            'Abu Dhabi', 'Dubai', 'Sharjah', 'Ajman', 
            'Umm Al Quwain', 'Ras Al Khaimah', 'Fujairah'
        ]
        
        logger.info("SyntheticDataGenerator initialized")

    def generate_application_data(self, count: int = 100) -> pd.DataFrame:
        """
        Generate synthetic application data.
        
        Args:
            count: Number of synthetic applications to generate
            
        Returns:
            DataFrame with synthetic application data
        """
        # Initialize lists for each column
        data = {
            'id': list(range(1, count + 1)),
            'filename': [f"application_{i:04d}.pdf" for i in range(1, count + 1)],
            'income': [],
            'family_size': [],
            'address': [],
            'assets': [],
            'liabilities': [],
            'employment_status': [],
            'validation_status': [],
            'assessment_status': [],
            'risk_level': [],
            'eligibility_score': [],
            'age': [],
            'gender': [],
            'nationality': [],
            'created_at': []
        }
        
        # Generate synthetic data for each application
        for i in range(count):
            # Choose income bracket
            income_bracket = random.choices(['low', 'medium', 'high'], weights=[0.5, 0.3, 0.2])[0]
            
            # Generate income
            mean, std = self.income_params[income_bracket]
            income = max(10000, np.random.normal(mean, std))
            data['income'].append(income)
            
            # Generate family size (more likely to be larger for lower income)
            if income_bracket == 'low':
                family_size = random.choices(range(1, 11), weights=[0.05, 0.1, 0.15, 0.2, 0.2, 0.1, 0.1, 0.05, 0.03, 0.02])[0]
            elif income_bracket == 'medium':
                family_size = random.choices(range(1, 8), weights=[0.1, 0.2, 0.3, 0.2, 0.1, 0.05, 0.05])[0]
            else:
                family_size = random.choices(range(1, 6), weights=[0.2, 0.3, 0.3, 0.15, 0.05])[0]
            
            data['family_size'].append(family_size)
            
            # Generate address
            emirate = random.choice(self.emirates)
            area = f"Area {random.randint(1, 50)}"
            street = f"Street {random.randint(1, 100)}"
            building = f"Building {random.randint(1, 200)}"
            address = f"{building}, {street}, {area}, {emirate}, UAE"
            data['address'].append(address)
            
            # Generate assets (correlated with income)
            assets_ratio = np.random.normal(3, 1)  # mean 3 years of income, std 1 year
            assets = max(0, income * assets_ratio)
            data['assets'].append(assets)
            
            # Generate liabilities (correlated with income and assets)
            liability_ratio = np.random.normal(0.3, 0.2)  # mean 30% of assets, std 20%
            liabilities = max(0, assets * liability_ratio)
            data['liabilities'].append(liabilities)
            
            # Generate employment status (correlated with income)
            if income_bracket == 'low':
                emp_weights = [0.3, 0.15, 0.3, 0.05, 0.1, 0.05, 0.05, 0]
            elif income_bracket == 'medium':
                emp_weights = [0.5, 0.2, 0.05, 0.05, 0.05, 0.1, 0.05, 0]
            else:
                emp_weights = [0.4, 0.2, 0, 0.05, 0, 0.05, 0.1, 0.2]
            
            employment_status = random.choices(self.employment_statuses, weights=emp_weights)[0]
            data['employment_status'].append(employment_status)
            
            # Generate age (between 18 and 70)
            age = random.randint(18, 70)
            data['age'].append(age)
            
            # Generate gender
            gender = random.choice(['Male', 'Female'])
            data['gender'].append(gender)
            
            # Generate nationality
            nationality = random.choice(self.nationalities)
            data['nationality'].append(nationality)
            
            # Calculate income per family member
            income_per_member = income / family_size
            
            # Calculate debt-to-income ratio
            debt_to_income = liabilities / income if income > 0 else 0
            
            # Determine risk level based on income, family size, and debt ratio
            risk_score = 0
            
            if income < 30000:
                risk_score += 3
            elif income < 50000:
                risk_score += 2
            elif income < 70000:
                risk_score += 1
                
            if family_size > 5:
                risk_score += 2
            elif family_size > 3:
                risk_score += 1
                
            if debt_to_income > 0.5:
                risk_score += 3
            elif debt_to_income > 0.3:
                risk_score += 2
            elif debt_to_income > 0.1:
                risk_score += 1
                
            if employment_status == 'Unemployed':
                risk_score += 3
                
            if risk_score >= 5:
                risk_level = 'high'
            elif risk_score >= 3:
                risk_level = 'medium'
            else:
                risk_level = 'low'
                
            data['risk_level'].append(risk_level)
            
            # Determine validation status
            # 90% of applications are valid
            is_valid = random.random() < 0.9
            validation_status = "✅ Valid" if is_valid else "❌ Invalid"
            data['validation_status'].append(validation_status)
            
            # Determine eligibility and assessment status
            if is_valid:
                # Calculate eligibility score
                eligibility_score = 0.0
                
                # Income factor
                if income_per_member < 5000:
                    eligibility_score += 0.4
                elif income_per_member < 10000:
                    eligibility_score += 0.3
                elif income_per_member < 15000:
                    eligibility_score += 0.2
                else:
                    eligibility_score += 0.1
                    
                # Family size factor
                if family_size >= 5:
                    eligibility_score += 0.2
                elif family_size >= 3:
                    eligibility_score += 0.15
                else:
                    eligibility_score += 0.1
                    
                # Employment status factor
                if employment_status == 'Unemployed':
                    eligibility_score += 0.3
                elif employment_status in ['Part-time', 'Student']:
                    eligibility_score += 0.2
                elif employment_status in ['Self-employed', 'Contract']:
                    eligibility_score += 0.15
                else:
                    eligibility_score += 0.1
                    
                # Age factor
                if age > 60 or age < 25:
                    eligibility_score += 0.1
                    
                # Random factor (10%)
                eligibility_score += random.uniform(0, 0.1)
                
                # Normalize to 0-1 range
                eligibility_score = min(1.0, eligibility_score)
                data['eligibility_score'].append(eligibility_score)
                
                # Determine assessment status based on eligibility score
                is_approved = eligibility_score >= 0.5
                assessment_status = "✅ Approved" if is_approved else "❌ Rejected"
            else:
                # Invalid applications are not assessed
                eligibility_score = 0.0
                data['eligibility_score'].append(eligibility_score)
                assessment_status = "❌ Rejected"
                
            data['assessment_status'].append(assessment_status)
            
            # Generate creation date (within the last year)
            days_ago = random.randint(1, 365)
            created_at = datetime.now() - timedelta(days=days_ago)
            data['created_at'].append(created_at)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        logger.info(f"Generated {count} synthetic applications")
        return df

    def generate_enablement_recommendations(self, application_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate synthetic enablement recommendations for an application.
        
        Args:
            application_data: Dictionary with application data
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Extract relevant application data
        income = application_data.get('income', 0)
        family_size = application_data.get('family_size', 0)
        employment_status = application_data.get('employment_status', '').lower()
        risk_level = application_data.get('risk_level', 'medium')
        age = application_data.get('age', 30)
        
        # Digital Skills Training
        if income < 50000 or 'unemployed' in employment_status:
            recommendations.append({
                "type": "upskilling",
                "priority": "high" if risk_level == "high" else "medium",
                "title": "Digital Skills Training Program",
                "description": "Free 12-week digital skills program covering basic IT, coding, and digital marketing",
                "eligibility": "Available to all applicants with income below 50,000 AED",
                "link": "https://example.gov/digital-skills"
            })
        
        # Job Placement
        if 'unemployed' in employment_status:
            recommendations.append({
                "type": "job_matching",
                "priority": "high",
                "title": "Government Job Placement Program",
                "description": "Fast-track placement program with local employers and government agencies",
                "eligibility": "Available to all unemployed applicants",
                "link": "https://example.gov/job-placement"
            })
        
        # Financial Management
        if risk_level in ["high", "medium"]:
            recommendations.append({
                "type": "financial_literacy",
                "priority": "medium",
                "title": "Financial Management Workshop",
                "description": "Workshop series on budgeting, saving, and debt management",
                "eligibility": "Available to all applicants",
                "link": "https://example.gov/financial-workshop"
            })
        
        # Small Business Support
        if 'self-employed' in employment_status or 'business' in employment_status:
            recommendations.append({
                "type": "business_support",
                "priority": "medium",
                "title": "Small Business Grant Program",
                "description": "Grants up to 50,000 AED for small business development or expansion",
                "eligibility": "Available to self-employed applicants or small business owners",
                "link": "https://example.gov/business-grants"
            })
        
        # Family Support
        if family_size >= 4:
            recommendations.append({
                "type": "family_support",
                "priority": "medium",
                "title": "Family Support Package",
                "description": "Additional benefits for large families including education subsidies and healthcare",
                "eligibility": "Available to families with 4 or more members",
                "link": "https://example.gov/family-support"
            })
        
        # Youth Programs
        if age < 30:
            recommendations.append({
                "type": "youth_program",
                "priority": "medium",
                "title": "Youth Leadership Program",
                "description": "Leadership development and mentorship program for young adults",
                "eligibility": "Available to applicants under 30 years of age",
                "link": "https://example.gov/youth-leadership"
            })
        
        # Senior Support
        if age > 55:
            recommendations.append({
                "type": "senior_support",
                "priority": "medium",
                "title": "Senior Citizen Support Program",
                "description": "Special assistance package for senior citizens including healthcare and social activities",
                "eligibility": "Available to applicants over 55 years of age",
                "link": "https://example.gov/senior-support"
            })
        
        return recommendations

    def generate_document_text(self, application_data: Dict[str, Any], doc_type: str) -> str:
        """
        Generate synthetic document text for testing OCR and extraction.
        
        Args:
            application_data: Dictionary with application data
            doc_type: Type of document to generate ('income', 'id', 'address', etc.)
            
        Returns:
            Generated document text
        """
        # Get relevant application data
        name = f"John Doe"  # Placeholder name
        income = application_data.get('income', 0)
        family_size = application_data.get('family_size', 0)
        address = application_data.get('address', '')
        employment_status = application_data.get('employment_status', '')
        nationality = application_data.get('nationality', 'UAE')
        
        # Generate document based on type
        if doc_type == 'income':
            # Income statement
            monthly_income = income / 12
            text = f"""
            INCOME STATEMENT
            -----------------------
            
            Name: {name}
            Employee ID: EMP{random.randint(10000, 99999)}
            
            Annual Income: AED {income:.2f}
            Monthly Salary: AED {monthly_income:.2f}
            
            Employment Status: {employment_status}
            Employment Duration: {random.randint(1, 15)} years
            
            This document certifies that the above individual has received
            the stated income for the financial year {datetime.now().year}.
            
            Authorized Signature: __________________
            Date: {datetime.now().strftime('%d/%m/%Y')}
            """
        
        elif doc_type == 'id':
            # Emirates ID
            id_number = f"{random.randint(100, 999)}-{random.randint(1000, 9999)}-{random.randint(1000000, 9999999)}-{random.randint(1, 9)}"
            expiry_date = (datetime.now() + timedelta(days=random.randint(30, 730))).strftime('%d/%m/%Y')
            
            text = f"""
            EMIRATES ID
            -----------------------
            
            Name: {name}
            Nationality: {nationality}
            ID Number: {id_number}
            Date of Birth: {random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(1950, 2000)}
            Gender: {random.choice(['Male', 'Female'])}
            Expiry Date: {expiry_date}
            
            Address: {address}
            
            This ID is the property of the UAE government.
            """
        
        elif doc_type == 'address':
            # Address proof (utility bill)
            account_number = f"ACC-{random.randint(10000, 99999)}"
            bill_amount = random.uniform(200, 1000)
            
            text = f"""
            UTILITY BILL
            -----------------------
            
            Customer Name: {name}
            Account Number: {account_number}
            
            Service Address: {address}
            
            Billing Period: {(datetime.now() - timedelta(days=30)).strftime('%d/%m/%Y')} to {datetime.now().strftime('%d/%m/%Y')}
            Total Amount Due: AED {bill_amount:.2f}
            
            Payment Due Date: {(datetime.now() + timedelta(days=14)).strftime('%d/%m/%Y')}
            
            This document serves as proof of residence at the above address.
            """
        
        elif doc_type == 'family':
            # Family document
            text = f"""
            FAMILY COMPOSITION CERTIFICATE
            -----------------------
            
            Head of Family: {name}
            National ID: {random.randint(1000000, 9999999)}
            
            Family Size: {family_size}
            
            Family Members:
            """
            
            for i in range(1, family_size):
                relation = random.choice(['Spouse', 'Child', 'Parent', 'Sibling'])
                age = random.randint(1, 70)
                gender = random.choice(['Male', 'Female'])
                
                text += f"""
            {i}. Relation: {relation}
               Age: {age}
               Gender: {gender}
               Residing at same address: {'Yes' if random.random() < 0.9 else 'No'}
                """
            
            text += f"""
            This document certifies that the above individuals are family members
            of the applicant as registered in the national database.
            
            Issuing Authority: Department of Family Affairs
            Date: {datetime.now().strftime('%d/%m/%Y')}
            """
        
        else:
            # Generic document
            text = f"""
            SUPPORTING DOCUMENT
            -----------------------
            
            Applicant Name: {name}
            Document Type: General Supporting Document
            Document ID: DOC-{random.randint(10000, 99999)}
            
            This document is submitted in support of the social security application.
            
            Date: {datetime.now().strftime('%d/%m/%Y')}
            """
        
        return text

    def save_to_csv(self, df: pd.DataFrame, file_path: str):
        """
        Save generated data to a CSV file.
        
        Args:
            df: DataFrame to save
            file_path: Path to save the CSV file
        """
        try:
            df.to_csv(file_path, index=False)
            logger.info(f"Saved synthetic data to {file_path}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")

    def save_to_json(self, data: Union[Dict, List], file_path: str):
        """
        Save generated data to a JSON file.
        
        Args:
            data: Data to save
            file_path: Path to save the JSON file
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved synthetic data to {file_path}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")


# Usage example
if __name__ == "__main__":
    # Create output directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Initialize generator
    generator = SyntheticDataGenerator(seed=42)
    
    # Generate application data
    applications = generator.generate_application_data(count=100)
    
    # Save to CSV
    generator.save_to_csv(applications, "data/synthetic_applications.csv")
    
    # Generate and save recommendations for a sample application
    sample_app = applications.iloc[0].to_dict()
    recommendations = generator.generate_enablement_recommendations(sample_app)
    generator.save_to_json(recommendations, "data/sample_recommendations.json")
    
    # Generate document text examples
    document_types = ['income', 'id', 'address', 'family']
    document_texts = {}
    
    for doc_type in document_types:
        text = generator.generate_document_text(sample_app, doc_type)
        document_texts[doc_type] = text
    
    generator.save_to_json(document_texts, "data/sample_documents.json")
