"""
Main FastAPI application for the Enhanced Social Security Application System.
Provides API endpoints for the Streamlit UI and orchestrates the agent workflow.
"""

import os
import uuid
import shutil
import logging
import tempfile
import uvicorn
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import json
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import agents
from agents.data_collector import DataCollectorAgent
from agents.validator import ValidatorAgent
from agents.assessor import AssessorAgent
from agents.counselor import CounselorAgent
from agents.orchestrator import OrchestratorAgent

# Import database models
from database.db_setup import Application, Document, Interaction, AuditLog, Recommendation, get_db, init_db

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("app")

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced Social Security Application System",
    description="API for automated social security application processing with AI agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Pydantic models for API requests and responses
class ApplicationSubmission(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    emirates_id: Optional[str] = None
    income: float
    family_size: int
    address: str
    employment_status: Optional[str] = None
    employer: Optional[str] = None
    job_title: Optional[str] = None
    employment_duration: Optional[int] = None
    monthly_expenses: Optional[float] = None
    assets_value: Optional[float] = None
    liabilities_value: Optional[float] = None

class ApplicationResponse(BaseModel):
    application_id: str
    message: str
    status: str

class ChatMessage(BaseModel):
    application_id: str
    message: str

class ChatResponse(BaseModel):
    text: str
    suggestions: List[str]
    agent: Optional[str] = None
    error: Optional[str] = None

class DocumentUpload(BaseModel):
    application_id: str
    document_type: str

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing application")
    init_db()
    logger.info("Database initialized")

# Application submission endpoint
@app.post("/api/applications", response_model=ApplicationResponse)
async def submit_application(application: ApplicationSubmission, background_tasks: BackgroundTasks):
    """Submit a new application for processing."""
    try:
        # Generate application ID
        application_id = str(uuid.uuid4())
        
        # Create application in database directly
        db = next(get_db())
        try:
            # Create new application
            new_application = Application(
                filename=application_id,  # Store the application_id in filename field
                name=application.name,
                email=application.email,
                phone=application.phone,
                emirates_id=application.emirates_id,
                income=application.income,
                family_size=application.family_size,
                address=application.address,
                employment_status=application.employment_status,
                employer=application.employer,
                job_title=application.job_title,
                employment_duration=application.employment_duration,
                monthly_expenses=application.monthly_expenses,
                assets_value=application.assets_value,
                liabilities_value=application.liabilities_value,
                validation_status="pending",
                assessment_status="pending",
                risk_level="unknown"
            )
            
            db.add(new_application)
            db.commit()
            
            # Prepare application data for processing
            app_data = application.dict()
            app_data["filename"] = application_id  # Use filename for compatibility
            
            # Initialize validator and assessor
            validator = ValidatorAgent()
            assessor = AssessorAgent()
            
            # Process in background
            background_tasks.add_task(process_application, app_data, new_application.id)
            
            return {
                "application_id": application_id,
                "message": "Application submitted successfully",
                "status": "processing"
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error submitting application: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Document upload endpoint
@app.post("/api/documents", response_model=Dict[str, Any])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    application_id: str = Form(...),
    document_type: str = Form(...)
):
    """Upload a document for an application."""
    try:
        # Validate document type
        valid_types = [
            "emirates_id", "bank_statement", "resume", 
            "assets_liabilities", "income_statement", "other"
        ]
        
        if document_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid document type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Create file path
        file_path = UPLOAD_DIR / f"{application_id}_{document_type}_{file.filename}"
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Process document in background
        background_tasks.add_task(process_document, str(file_path), file.filename, document_type, application_id)
        
        return {
            "message": f"Document uploaded successfully: {file.filename}",
            "document_type": document_type,
            "file_path": str(file_path),
            "application_id": application_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Handle chat messages for an application."""
    try:
        # Log the incoming chat request
        logger.info(f"Received chat request for application ID: {message.application_id}, message: {message.message}")
        
        # Initialize orchestrator
        orchestrator = OrchestratorAgent()
        
        # Process chat message
        logger.info(f"Sending message to orchestrator")
        response = await orchestrator.handle_chat_message(message.application_id, message.message)
        
        # Log the response from orchestrator
        logger.info(f"Received response from orchestrator: {response}")
        
        if "error" in response and response["error"]:
            logger.error(f"Error in response: {response['error']}")
            raise HTTPException(status_code=404, detail=response["error"])
        
        # Log successful response
        logger.info(f"Returning successful response")
        return response
    except HTTPException as he:
        logger.error(f"HTTP Exception in chat endpoint: {str(he)}")
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error processing chat message: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail=str(e))

# Get application status endpoint
@app.get("/api/applications/{application_id}", response_model=Dict[str, Any])
async def get_application_status(application_id: str, db=Depends(get_db)):
    """Get status and details of an application."""
    try:
        # Query application by filename (which stores application_id)
        application = db.query(Application).filter(
            Application.filename == application_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail=f"Application with ID {application_id} not found")
        
        # Get recommendations
        from database.db_setup import Recommendation
        recommendations = db.query(Recommendation).filter(
            Recommendation.application_id == application.id
        ).all()
        
        # Format recommendations
        rec_list = [
            {
                "category": rec.category,
                "priority": rec.priority,
                "description": rec.description,
                "action_items": rec.action_items
            }
            for rec in recommendations
        ]
        
        # Get documents
        documents = db.query(Document).filter(
            Document.application_id == application.id
        ).all()
        
        # Format documents
        doc_list = [
            {
                "document_type": doc.document_type,
                "filename": doc.filename,
                "uploaded_at": doc.uploaded_at.isoformat()
            }
            for doc in documents
        ]
        
        # Return application details
        return {
            "application_id": application.filename,  # Use filename as application_id
            "name": application.name,
            "email": application.email,
            "phone": application.phone,
            "income": application.income,
            "family_size": application.family_size,
            "address": application.address,
            "validation_status": application.validation_status,
            "assessment_status": application.assessment_status,
            "risk_level": application.risk_level,
            "created_at": application.created_at.isoformat(),
            "updated_at": application.updated_at.isoformat(),
            "recommendations": rec_list,
            "documents": doc_list
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get all applications endpoint (admin only)
@app.get("/api/applications", response_model=List[Dict[str, Any]])
async def get_all_applications(limit: int = 20, offset: int = 0, db=Depends(get_db)):
    """Get all applications (admin only)."""
    try:
        # Query applications
        applications = db.query(Application).order_by(
            Application.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        # Format applications
        app_list = [
            {
                "application_id": app.application_id,
                "name": app.name,
                "income": app.income,
                "family_size": app.family_size,
                "validation_status": app.validation_status,
                "assessment_status": app.assessment_status,
                "risk_level": app.risk_level,
                "created_at": app.created_at.isoformat()
            }
            for app in applications
        ]
        
        return app_list
    except Exception as e:
        logger.error(f"Error getting applications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Generate explanation endpoint
@app.get("/api/applications/{application_id}/explanation", response_model=Dict[str, Any])
async def get_explanation(application_id: str, db=Depends(get_db)):
    """Get detailed explanation for an application decision."""
    try:
        # Query application
        application = db.query(Application).filter(
            Application.filename == application_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail=f"Application with ID {application_id} not found")
        
        # Initialize counselor
        counselor = CounselorAgent()
        
        # Format application data
        app_data = {
            "application_id": application.application_id,
            "name": application.name,
            "income": application.income,
            "family_size": application.family_size,
            "address": application.address,
            "validation_status": application.validation_status,
            "assessment_status": application.assessment_status,
            "risk_level": application.risk_level
        }
        
        # Generate explanation
        explanation = counselor.explain_decision(app_data)
        
        return explanation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task to process applications
async def process_application(app_data: Dict[str, Any], application_id: int):
    """Process an application in the background."""
    try:
        logger.info(f"Processing application: {app_data.get('name')}")
        
        # Get database session
        db = next(get_db())
        
        try:
            # Get application
            application = db.query(Application).filter(
                Application.id == application_id
            ).first()
            
            if not application:
                logger.warning(f"Application with ID {application_id} not found")
                return
            
            # Validate application
            validator = ValidatorAgent()
            
            # Format application data for validator
            validation_data = {
                "filename": application.filename,
                "name": application.name,
                "email": application.email,
                "phone": application.phone,
                "emirates_id": application.emirates_id,
                "income": application.income,
                "family_size": application.family_size,
                "address": application.address,
                "employment_status": application.employment_status,
                "employer": application.employer,
                "job_title": application.job_title,
                "employment_duration": application.employment_duration,
                "monthly_expenses": application.monthly_expenses,
                "assets_value": application.assets_value,
                "liabilities_value": application.liabilities_value
            }
            
            # Validate application
            is_valid, errors = validator.validate(validation_data)
            
            # Update validation status
            application.validation_status = "valid" if is_valid else "invalid"
            db.commit()
            
            # If valid, assess application
            if is_valid:
                assessor = AssessorAgent()
                is_approved, reasons, assessment_details = assessor.assess_application(validation_data)
                
                # Update assessment status
                application.assessment_status = "approved" if is_approved else "rejected"
                application.risk_level = assessment_details['risk_level']
                db.commit()
                
                # Generate recommendations using counselor
                try:
                    counselor = CounselorAgent()
                    recommendations = counselor.generate_recommendations(validation_data)
                    
                    # Save recommendations to database
                    for rec in recommendations:
                        db_rec = Recommendation(
                            application_id=application.id,
                            category=rec.get("category", "General"),
                            priority=rec.get("priority", "medium"),
                            description=rec.get("description", ""),
                            action_items=rec.get("action_items", [])
                        )
                        db.add(db_rec)
                    
                    db.commit()
                except Exception as rec_error:
                    logger.error(f"Error generating recommendations: {str(rec_error)}")
                    # Continue processing even if recommendations fail
            
            logger.info(f"Application processing completed for {application.filename}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error processing application: {str(e)}")

# Background task to process uploaded documents
async def process_document(file_path: str, filename: str, document_type: str, application_id: str):
    """Process an uploaded document and update application data."""
    try:
        logger.info(f"Processing document: {filename} for application {application_id}")
        
        # Initialize data collector
        collector = DataCollectorAgent()
        
        # Process document
        extracted_data = collector.process_document(file_path, filename, document_type)
        
        # Get database session
        db = next(get_db())
        
        try:
            # Get application by filename (which contains the application_id)
            application = db.query(Application).filter(
                Application.filename == application_id
            ).first()
            
            if not application:
                logger.warning(f"Application with ID {application_id} not found")
                return
            
            # Link document to application
            document = db.query(Document).filter(
                Document.file_path == file_path
            ).first()
            
            if document:
                document.application_id = application.id
                db.commit()
            
            # Update application with extracted data
            for key, value in extracted_data.items():
                if hasattr(application, key) and getattr(application, key) is None:
                    setattr(application, key, value)
            
            db.commit()
            
            # Re-validate application
            validator = ValidatorAgent()
            
            # Format application data
            validation_data = {
                "filename": application.filename,
                "name": application.name,
                "email": application.email,
                "phone": application.phone,
                "emirates_id": application.emirates_id,
                "income": application.income,
                "family_size": application.family_size,
                "address": application.address,
                "employment_status": application.employment_status,
                "employer": application.employer,
                "job_title": application.job_title,
                "employment_duration": application.employment_duration,
                "monthly_expenses": application.monthly_expenses,
                "assets_value": application.assets_value,
                "liabilities_value": application.liabilities_value
            }
            
            # Validate application
            is_valid, errors = validator.validate(validation_data)
            
            # Update validation status
            application.validation_status = "valid" if is_valid else "invalid"
            db.commit()
            
            # If valid, assess application
            if is_valid:
                assessor = AssessorAgent()
                is_approved, reasons, assessment_details = assessor.assess_application(validation_data)
                
                # Update assessment status
                application.assessment_status = "approved" if is_approved else "rejected"
                application.risk_level = assessment_details['risk_level']
                db.commit()
                
                # Generate recommendations
                counselor = CounselorAgent()
                counselor.generate_recommendations(validation_data)
            
            logger.info(f"Document processing completed for {filename}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")

# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
