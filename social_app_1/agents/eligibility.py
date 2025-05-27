"""
Eligibility Agent - ML-powered eligibility assessment for social support applications.
"""

import logging
import json
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# For ML model integration
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()

# PostgreSQL connection configuration
DB_USER = os.getenv('DB_USER', 'amarjeet')
DB_PASSWORD = os.getenv('DB_PASSWORD', '9582924264')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'social')

# Construct database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800  # Recycle connections after 30 minutes
)

SessionLocal = sessionmaker(bind=engine)

class Application(Base):
    """SQLAlchemy model for applications."""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    income = Column(Float, nullable=False)
    family_size = Column(Integer, nullable=False)
    address = Column(Text, nullable=False)
    assets = Column(Float, nullable=True)
    liabilities = Column(Float, nullable=True)
    employment_status = Column(String(100), nullable=True)
    validation_status = Column(String(50), nullable=False)
    assessment_status = Column(String(50), nullable=False)
    risk_level = Column(String(50), nullable=False)
    eligibility_score = Column(Float, nullable=True)
    enablement_recommendations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Application(id={self.id}, filename='{self.filename}', status='{self.assessment_status}')>"


class EligibilityAgent:
    """
    Agent that assesses eligibility for social support using ML models
    and provides recommendations for financial support and economic enablement.
    """
    
    def __init__(self, model_type: str = "random_forest"):
        """
        Initialize the eligibility agent with ML models and assessment criteria.
        
        Args:
            model_type: Type of ML model to use ('random_forest', 'gradient_boosting', or 'logistic')
        """
        self.db = SessionLocal()
        
        # Thresholds for risk assessment
        self.risk_thresholds = {
            'income': 50000,  # AED
            'family_size': 5,
            'min_income_per_member': 10000,  # AED
            'debt_to_income_ratio': 0.5  # 50% of income
        }
        
        # Initialize ML models
        self.model_type = model_type
        self.model = self._initialize_model()
        self.scaler = StandardScaler()
        
        # Train model with synthetic data if available
        self._train_model_with_synthetic_data()
        
        logger.info(f"EligibilityAgent initialized with {model_type} model")

    def _initialize_model(self):
        """
        Initialize the ML model based on the selected type.
        
        Returns:
            Initialized ML model
        """
        if self.model_type == "random_forest":
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
        elif self.model_type == "gradient_boosting":
            return GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
        elif self.model_type == "logistic":
            return LogisticRegression(
                C=1.0,
                solver='liblinear',
                random_state=42,
                class_weight='balanced'
            )
        else:
            logger.warning(f"Unknown model type: {self.model_type}, defaulting to RandomForest")
            return RandomForestClassifier(n_estimators=100, random_state=42)

    def _train_model_with_synthetic_data(self):
        """
        Train the ML model with synthetic data for eligibility assessment.
        """
        try:
            # Generate synthetic data if no existing data is available
            synthetic_data = self._generate_synthetic_training_data(1000)
            
            # Prepare features and target
            X = synthetic_data[['income', 'family_size', 'income_per_member', 
                               'debt_to_income_ratio', 'assets_to_income_ratio']]
            y = synthetic_data['is_eligible']
            
            # Split data and train model
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            
            logger.info(f"Model trained with synthetic data")
            logger.info(f"Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, "
                       f"Recall: {recall:.4f}, F1: {f1:.4f}")
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")

    def _generate_synthetic_training_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """
        Generate synthetic training data for model training.
        
        Args:
            n_samples: Number of synthetic samples to generate
            
        Returns:
            DataFrame with synthetic data
        """
        np.random.seed(42)
        
        # Generate random features
        income = np.random.lognormal(mean=11, sigma=0.7, size=n_samples)  # Income in AED
        family_size = np.random.randint(1, 10, size=n_samples)
        assets = np.random.lognormal(mean=12, sigma=1.0, size=n_samples)
        liabilities = np.random.lognormal(mean=10, sigma=1.2, size=n_samples)
        
        # Calculate derived features
        income_per_member = income / family_size
        debt_to_income_ratio = liabilities / income
        assets_to_income_ratio = assets / income
        
        # Create synthetic eligibility based on rules
        is_eligible = np.zeros(n_samples, dtype=int)
        
        for i in range(n_samples):
            # Eligibility criteria
            if (income_per_member[i] < 15000 and 
                debt_to_income_ratio[i] < 0.7 and 
                family_size[i] >= 2):
                is_eligible[i] = 1
            elif (income_per_member[i] < 10000 and 
                  debt_to_income_ratio[i] < 0.5):
                is_eligible[i] = 1
            elif (income[i] < 30000 and 
                  family_size[i] >= 4 and 
                  assets_to_income_ratio[i] < 2):
                is_eligible[i] = 1
                
            # Add some noise (10% random flips)
            if np.random.random() < 0.1:
                is_eligible[i] = 1 - is_eligible[i]
        
        # Create DataFrame
        data = pd.DataFrame({
            'income': income,
            'family_size': family_size,
            'income_per_member': income_per_member,
            'assets': assets,
            'liabilities': liabilities,
            'debt_to_income_ratio': debt_to_income_ratio,
            'assets_to_income_ratio': assets_to_income_ratio,
            'is_eligible': is_eligible
        })
        
        return data

    def assess_application(self, data: Dict) -> Tuple[bool, List[str], Dict]:
        """
        Assess an application for eligibility using ML models and rule-based criteria.
        
        Args:
            data: Dictionary containing application data
            
        Returns:
            Tuple of (is_eligible, reasons, assessment_details)
        """
        # Extract data fields
        income = data.get('income', 0)
        family_size = data.get('family_size', 0)
        assets = data.get('assets', 0)
        liabilities = data.get('liabilities', 0)
        
        # Calculate derived metrics
        income_per_member = income / family_size if family_size > 0 else 0
        debt_to_income_ratio = liabilities / income if income > 0 else 0
        assets_to_income_ratio = assets / income if income > 0 else 0
        
        # Prepare feature vector for ML model
        features = [[
            income, 
            family_size, 
            income_per_member,
            debt_to_income_ratio,
            assets_to_income_ratio
        ]]
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Get ML model prediction
        ml_eligibility_score = self.model.predict_proba(features_scaled)[0][1]
        ml_is_eligible = ml_eligibility_score >= 0.6  # Threshold for eligibility
        
        # Calculate risk level
        risk_level = self._calculate_risk_level(data)
        
        # Get enablement recommendations
        enablement_recommendations = self._generate_enablement_recommendations(data, risk_level)
        
        # Rule-based assessment
        reasons = []
        rule_based_is_eligible = True
        
        # Check income threshold
        if income < self.risk_thresholds['income']:
            reasons.append("Income below threshold")
            rule_based_is_eligible = False
        
        # Check family size
        if family_size > self.risk_thresholds['family_size']:
            reasons.append("Large family size")
            rule_based_is_eligible = False
        
        # Check income per family member
        if income_per_member < self.risk_thresholds['min_income_per_member']:
            reasons.append("Low income per family member")
            rule_based_is_eligible = False
        
        # Check debt to income ratio
        if debt_to_income_ratio > self.risk_thresholds['debt_to_income_ratio']:
            reasons.append("High debt-to-income ratio")
            rule_based_is_eligible = False
        
        # Final decision (combine ML and rule-based)
        # For this implementation, we'll use a weighted approach
        # 60% ML model, 40% rule-based
        is_eligible = (ml_is_eligible * 0.6) + (rule_based_is_eligible * 0.4) >= 0.5
        
        # Prepare assessment details
        assessment_details = {
            'risk_level': risk_level,
            'income_per_member': income_per_member,
            'debt_to_income_ratio': debt_to_income_ratio,
            'assets_to_income_ratio': assets_to_income_ratio,
            'ml_eligibility_score': ml_eligibility_score,
            'assessment_date': datetime.utcnow().isoformat(),
            'enablement_recommendations': enablement_recommendations
        }
        
        # Store in database
        self._store_assessment(data, assessment_details, is_eligible)
        
        return is_eligible, reasons, assessment_details

    def _calculate_risk_level(self, data: Dict) -> str:
        """
        Calculate risk level based on application data.
        
        Args:
            data: Dictionary containing application data
            
        Returns:
            Risk level string ('low', 'medium', or 'high')
        """
        risk_score = 0
        income = data.get('income', 0)
        family_size = data.get('family_size', 0)
        liabilities = data.get('liabilities', 0)
        
        # Income risk
        if income < 30000:
            risk_score += 3
        elif income < 50000:
            risk_score += 2
        elif income < 70000:
            risk_score += 1
        
        # Family size risk
        if family_size > 5:
            risk_score += 2
        elif family_size > 3:
            risk_score += 1
        
        # Debt risk
        debt_to_income = liabilities / income if income > 0 else 0
        if debt_to_income > 0.5:
            risk_score += 3
        elif debt_to_income > 0.3:
            risk_score += 2
        elif debt_to_income > 0.1:
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 5:
            return "high"
        elif risk_score >= 3:
            return "medium"
        return "low"

    def _generate_enablement_recommendations(self, data: Dict, risk_level: str) -> List[Dict]:
        """
        Generate economic enablement recommendations based on application data.
        
        Args:
            data: Dictionary containing application data
            risk_level: Calculated risk level ('low', 'medium', or 'high')
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        income = data.get('income', 0)
        family_size = data.get('family_size', 0)
        employment_status = data.get('employment_status', 'Unknown')
        
        # Upskilling recommendations
        if 'unemployed' in employment_status.lower() or income < 40000:
            recommendations.append({
                "type": "upskilling",
                "priority": "high" if risk_level == "high" else "medium",
                "title": "Digital Skills Training Program",
                "description": "Free 12-week digital skills program covering basic IT, coding, and digital marketing",
                "eligibility": "Available to all applicants with income below 40,000 AED",
                "link": "https://example.gov/digital-skills"
            })
        
        # Job matching
        if 'unemployed' in employment_status.lower() or 'seeking' in employment_status.lower():
            recommendations.append({
                "type": "job_matching",
                "priority": "high",
                "title": "Government Job Placement Program",
                "description": "Fast-track placement program with local employers and government agencies",
                "eligibility": "Available to all unemployed applicants",
                "link": "https://example.gov/job-placement"
            })
        
        # Financial literacy
        if risk_level == "high" or risk_level == "medium":
            recommendations.append({
                "type": "financial_literacy",
                "priority": "medium",
                "title": "Financial Management Workshop",
                "description": "Workshop series on budgeting, saving, and debt management",
                "eligibility": "Available to all applicants",
                "link": "https://example.gov/financial-workshop"
            })
        
        # Small business support
        if 'self-employed' in employment_status.lower() or 'business' in employment_status.lower():
            recommendations.append({
                "type": "business_support",
                "priority": "medium",
                "title": "Small Business Grant Program",
                "description": "Grants up to 50,000 AED for small business development or expansion",
                "eligibility": "Available to self-employed applicants or small business owners",
                "link": "https://example.gov/business-grants"
            })
        
        # Family support
        if family_size >= 4:
            recommendations.append({
                "type": "family_support",
                "priority": "medium",
                "title": "Family Support Package",
                "description": "Additional benefits for large families including education subsidies and healthcare",
                "eligibility": "Available to families with 4 or more members",
                "link": "https://example.gov/family-support"
            })
        
        return recommendations

    def _store_assessment(self, data: Dict, assessment_details: Dict, is_eligible: bool):
        """
        Store assessment results in the database.
        
        Args:
            data: Dictionary containing application data
            assessment_details: Dictionary containing assessment details
            is_eligible: Boolean indicating eligibility
        """
        try:
            # Convert enablement recommendations to JSON string
            enablement_json = json.dumps(assessment_details.get('enablement_recommendations', []))
            
            application = Application(
                filename=data['filename'],
                income=data.get('income', 0),
                family_size=data.get('family_size', 0),
                address=data.get('address', ''),
                assets=data.get('assets', 0),
                liabilities=data.get('liabilities', 0),
                employment_status=data.get('employment_status', ''),
                validation_status=data.get('validation_status', 'Unknown'),
                assessment_status="approved" if is_eligible else "rejected",
                risk_level=assessment_details['risk_level'],
                eligibility_score=assessment_details.get('ml_eligibility_score', 0),
                enablement_recommendations=enablement_json
            )

            self.db.add(application)
            self.db.commit()
            
            logger.info(f"Assessment stored for {data['filename']}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to store assessment: {str(e)}")

    def get_recent_assessments(self, limit: int = 10) -> List[Dict]:
        """
        Retrieve recent assessments from the database.
        
        Args:
            limit: Maximum number of records to retrieve
            
        Returns:
            List of assessment dictionaries
        """
        try:
            applications = self.db.query(Application).order_by(
                Application.created_at.desc()
            ).limit(limit).all()

            return [
                {
                    'id': app.id,
                    'filename': app.filename,
                    'income': app.income,
                    'family_size': app.family_size,
                    'address': app.address,
                    'assets': app.assets,
                    'liabilities': app.liabilities,
                    'employment_status': app.employment_status,
                    'validation_status': app.validation_status,
                    'assessment_status': app.assessment_status,
                    'risk_level': app.risk_level,
                    'eligibility_score': app.eligibility_score,
                    'enablement_recommendations': json.loads(app.enablement_recommendations) 
                        if app.enablement_recommendations else [],
                    'created_at': app.created_at.isoformat()
                }
                for app in applications
            ]
        except Exception as e:
            logger.error(f"Error retrieving assessments: {str(e)}")
            return []

    def __del__(self):
        """Close database connection when the agent is destroyed."""
        try:
            self.db.close()
        except:
            pass
