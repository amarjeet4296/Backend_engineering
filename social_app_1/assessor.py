from typing import Dict, List, Tuple
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database setup
Base = declarative_base()
metadata = MetaData()

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
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    income = Column(Float, nullable=False)
    family_size = Column(Integer, nullable=False)
    address = Column(Text, nullable=False)
    validation_status = Column(String(50), nullable=False)
    assessment_status = Column(String(50), nullable=False)
    risk_level = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Application(id={self.id}, filename='{self.filename}', status='{self.assessment_status}')>"

def init_db():
    """Initialize the database and create tables if they don't exist"""
    try:
        # Drop existing tables if they exist
        Base.metadata.drop_all(bind=engine)
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise

# Initialize database
init_db()

class AssessorAgent:
    def __init__(self):
        self.db = SessionLocal()
        self.risk_thresholds = {
            'income': 50000,  # AED
            'family_size': 5,
            'min_income_per_member': 10000  # AED
        }

    def assess_application(self, data: Dict) -> Tuple[bool, List[str], Dict]:
        """
        Assess an application after validation.
        Returns: (is_approved, reasons, assessment_details)
        """
        assessment_details = {
            'risk_level': self._calculate_risk_level(data),
            'income_per_member': data['income'] / data['family_size'] if data['family_size'] > 0 else 0,
            'assessment_date': datetime.utcnow().isoformat()
        }

        reasons = []
        is_approved = True

        # Check income threshold
        if data['income'] < self.risk_thresholds['income']:
            reasons.append("Income below threshold")
            is_approved = False

        # Check family size
        if data['family_size'] > self.risk_thresholds['family_size']:
            reasons.append("Large family size")
            is_approved = False

        # Check income per family member
        if assessment_details['income_per_member'] < self.risk_thresholds['min_income_per_member']:
            reasons.append("Low income per family member")
            is_approved = False

        # Store in database
        self._store_assessment(data, assessment_details, is_approved)

        return is_approved, reasons, assessment_details

    def _calculate_risk_level(self, data: Dict) -> str:
        """
        Calculate risk level based on application data
        """
        risk_score = 0

        # Income risk
        if data['income'] < 30000:
            risk_score += 3
        elif data['income'] < 50000:
            risk_score += 2
        elif data['income'] < 70000:
            risk_score += 1

        # Family size risk
        if data['family_size'] > 5:
            risk_score += 2
        elif data['family_size'] > 3:
            risk_score += 1

        # Determine risk level
        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        return "low"

    def _store_assessment(self, data: Dict, assessment_details: Dict, is_approved: bool):
        """
        Store assessment results in the database
        """
        try:
            application = Application(
                filename=data['filename'],
                income=data['income'],
                family_size=data['family_size'],
                address=data['address'],
                validation_status=data['validation_status'],
                assessment_status="approved" if is_approved else "rejected",
                risk_level=assessment_details['risk_level']
            )

            self.db.add(application)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to store assessment: {str(e)}")

    def get_recent_assessments(self, limit: int = 10) -> List[Dict]:
        """
        Retrieve recent assessments from the database
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
                    'validation_status': app.validation_status,
                    'assessment_status': app.assessment_status,
                    'risk_level': app.risk_level,
                    'created_at': app.created_at.isoformat()
                }
                for app in applications
            ]
        except Exception as e:
            print(f"Error retrieving assessments: {str(e)}")
            return []  # Return empty list instead of raising exception

    def __del__(self):
        """
        Close database connection when the agent is destroyed
        """
        self.db.close() 