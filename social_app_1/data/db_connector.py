"""
Database Connector - Handles PostgreSQL integration and data persistence
for the social security application system.
"""

import logging
import os
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, Boolean, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import select, func
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_USER = os.getenv('DB_USER', 'amarjeet')
DB_PASSWORD = os.getenv('DB_PASSWORD', '9582924264')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'social')

# Construct database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create base class for declarative models
Base = declarative_base()

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
    demographic_info = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Application(id={self.id}, filename='{self.filename}', status='{self.assessment_status}')>"


class Document(Base):
    """SQLAlchemy model for processed documents."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, nullable=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    extracted_data = Column(Text, nullable=True)
    processing_status = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', type='{self.file_type}')>"


class DatabaseConnector:
    """
    Manages database connections and operations for the social security application system.
    Provides an interface for storing and retrieving application data.
    """
    
    def __init__(self):
        """
        Initialize the database connector and create tables if they don't exist.
        """
        try:
            # Create engine with connection pooling
            self.engine = create_engine(
                DATABASE_URL,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800  # Recycle connections after 30 minutes
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create all tables in the database
            Base.metadata.create_all(bind=self.engine)
            
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise

    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy Session object
        """
        return self.SessionLocal()

    def store_application(self, app_data: Dict[str, Any]) -> int:
        """
        Store an application in the database.
        
        Args:
            app_data: Dictionary containing application data
            
        Returns:
            ID of the created application record
        """
        try:
            # Create session
            db = self.get_session()
            
            # Convert enablement recommendations to JSON string if present
            if 'enablement_recommendations' in app_data and isinstance(app_data['enablement_recommendations'], (list, dict)):
                app_data['enablement_recommendations'] = json.dumps(app_data['enablement_recommendations'])
            
            # Convert demographic info to JSON string if present
            if 'demographic_info' in app_data and isinstance(app_data['demographic_info'], dict):
                app_data['demographic_info'] = json.dumps(app_data['demographic_info'])
            
            # Create application object
            application = Application(**app_data)
            
            # Add to session and commit
            db.add(application)
            db.commit()
            db.refresh(application)
            
            app_id = application.id
            logger.info(f"Stored application with ID: {app_id}")
            
            # Close session
            db.close()
            
            return app_id
        
        except Exception as e:
            logger.error(f"Error storing application: {str(e)}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return -1

    def store_document(self, doc_data: Dict[str, Any]) -> int:
        """
        Store a document in the database.
        
        Args:
            doc_data: Dictionary containing document data
            
        Returns:
            ID of the created document record
        """
        try:
            # Create session
            db = self.get_session()
            
            # Convert extracted_data to JSON string if it's a dictionary
            if 'extracted_data' in doc_data and isinstance(doc_data['extracted_data'], dict):
                doc_data['extracted_data'] = json.dumps(doc_data['extracted_data'])
            
            # Create document object
            document = Document(**doc_data)
            
            # Add to session and commit
            db.add(document)
            db.commit()
            db.refresh(document)
            
            doc_id = document.id
            logger.info(f"Stored document with ID: {doc_id}")
            
            # Close session
            db.close()
            
            return doc_id
        
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return -1

    def get_application(self, app_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an application by ID.
        
        Args:
            app_id: Application ID
            
        Returns:
            Dictionary with application data or None if not found
        """
        try:
            # Create session
            db = self.get_session()
            
            # Query the application
            application = db.query(Application).filter(Application.id == app_id).first()
            
            if not application:
                logger.warning(f"Application with ID {app_id} not found")
                db.close()
                return None
            
            # Convert to dictionary
            app_dict = {
                'id': application.id,
                'filename': application.filename,
                'income': application.income,
                'family_size': application.family_size,
                'address': application.address,
                'assets': application.assets,
                'liabilities': application.liabilities,
                'employment_status': application.employment_status,
                'validation_status': application.validation_status,
                'assessment_status': application.assessment_status,
                'risk_level': application.risk_level,
                'eligibility_score': application.eligibility_score,
                'created_at': application.created_at.isoformat(),
                'updated_at': application.updated_at.isoformat()
            }
            
            # Parse JSON fields
            if application.enablement_recommendations:
                try:
                    app_dict['enablement_recommendations'] = json.loads(application.enablement_recommendations)
                except:
                    app_dict['enablement_recommendations'] = application.enablement_recommendations
            
            if application.demographic_info:
                try:
                    app_dict['demographic_info'] = json.loads(application.demographic_info)
                except:
                    app_dict['demographic_info'] = application.demographic_info
            
            # Close session
            db.close()
            
            return app_dict
        
        except Exception as e:
            logger.error(f"Error retrieving application: {str(e)}")
            if 'db' in locals():
                db.close()
            return None

    def get_recent_applications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent applications.
        
        Args:
            limit: Maximum number of applications to retrieve
            
        Returns:
            List of application dictionaries
        """
        try:
            # Create session
            db = self.get_session()
            
            # Query recent applications
            applications = db.query(Application).order_by(
                Application.created_at.desc()
            ).limit(limit).all()
            
            # Convert to list of dictionaries
            result = []
            for app in applications:
                app_dict = {
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
                result.append(app_dict)
            
            # Close session
            db.close()
            
            return result
        
        except Exception as e:
            logger.error(f"Error retrieving recent applications: {str(e)}")
            if 'db' in locals():
                db.close()
            return []

    def get_application_documents(self, app_id: int) -> List[Dict[str, Any]]:
        """
        Get documents associated with an application.
        
        Args:
            app_id: Application ID
            
        Returns:
            List of document dictionaries
        """
        try:
            # Create session
            db = self.get_session()
            
            # Query documents for the application
            documents = db.query(Document).filter(
                Document.application_id == app_id
            ).order_by(Document.created_at.desc()).all()
            
            # Convert to list of dictionaries
            result = []
            for doc in documents:
                doc_dict = {
                    'id': doc.id,
                    'filename': doc.filename,
                    'file_type': doc.file_type,
                    'file_size': doc.file_size,
                    'processing_status': doc.processing_status,
                    'created_at': doc.created_at.isoformat()
                }
                
                # Parse extracted data if available
                if doc.extracted_data:
                    try:
                        doc_dict['extracted_data'] = json.loads(doc.extracted_data)
                    except:
                        doc_dict['extracted_data'] = doc.extracted_data
                
                result.append(doc_dict)
            
            # Close session
            db.close()
            
            return result
        
        except Exception as e:
            logger.error(f"Error retrieving application documents: {str(e)}")
            if 'db' in locals():
                db.close()
            return []

    def update_application(self, app_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Update an application record.
        
        Args:
            app_id: Application ID
            update_data: Dictionary with fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create session
            db = self.get_session()
            
            # Query the application
            application = db.query(Application).filter(Application.id == app_id).first()
            
            if not application:
                logger.warning(f"Application with ID {app_id} not found for update")
                db.close()
                return False
            
            # Convert complex data structures to JSON
            if 'enablement_recommendations' in update_data and isinstance(update_data['enablement_recommendations'], (list, dict)):
                update_data['enablement_recommendations'] = json.dumps(update_data['enablement_recommendations'])
            
            if 'demographic_info' in update_data and isinstance(update_data['demographic_info'], dict):
                update_data['demographic_info'] = json.dumps(update_data['demographic_info'])
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(application, key):
                    setattr(application, key, value)
            
            # Update the updated_at timestamp
            application.updated_at = datetime.utcnow()
            
            # Commit changes
            db.commit()
            logger.info(f"Updated application with ID: {app_id}")
            
            # Close session
            db.close()
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating application: {str(e)}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return False

    def get_application_statistics(self) -> Dict[str, Any]:
        """
        Get statistics on applications in the database.
        
        Returns:
            Dictionary with application statistics
        """
        try:
            # Create session
            db = self.get_session()
            
            # Calculate statistics
            stats = {}
            
            # Total applications
            stats['total_applications'] = db.query(func.count(Application.id)).scalar()
            
            # Applications by status
            status_counts = db.query(
                Application.assessment_status, 
                func.count(Application.id)
            ).group_by(Application.assessment_status).all()
            
            stats['status_counts'] = {status: count for status, count in status_counts}
            
            # Applications by risk level
            risk_counts = db.query(
                Application.risk_level, 
                func.count(Application.id)
            ).group_by(Application.risk_level).all()
            
            stats['risk_counts'] = {risk: count for risk, count in risk_counts}
            
            # Average income
            stats['avg_income'] = db.query(func.avg(Application.income)).scalar()
            
            # Average family size
            stats['avg_family_size'] = db.query(func.avg(Application.family_size)).scalar()
            
            # Close session
            db.close()
            
            return stats
        
        except Exception as e:
            logger.error(f"Error retrieving application statistics: {str(e)}")
            if 'db' in locals():
                db.close()
            return {}

    def export_applications_to_dataframe(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Export applications to a pandas DataFrame.
        
        Args:
            filters: Optional dictionary of filters to apply
            
        Returns:
            DataFrame containing application data
        """
        try:
            # Create session
            db = self.get_session()
            
            # Base query
            query = db.query(Application)
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    if hasattr(Application, key):
                        query = query.filter(getattr(Application, key) == value)
            
            # Execute query
            applications = query.all()
            
            # Convert to dataframe
            data = []
            for app in applications:
                app_dict = {
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
                    'created_at': app.created_at,
                    'updated_at': app.updated_at
                }
                data.append(app_dict)
            
            df = pd.DataFrame(data)
            
            # Close session
            db.close()
            
            return df
        
        except Exception as e:
            logger.error(f"Error exporting applications to dataframe: {str(e)}")
            if 'db' in locals():
                db.close()
            return pd.DataFrame()

    def __del__(self):
        """
        Clean up database resources when the connector is destroyed.
        """
        try:
            self.engine.dispose()
            logger.info("Database connection closed")
        except:
            pass
