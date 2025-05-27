"""
Simple Orchestrator Agent - Coordinates the workflow between existing agents
using a straightforward sequential approach without external dependencies.
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

# Import existing agents
from data_collector import DataCollector
from validator import ValidatorAgent
from assessor import AssessorAgent
from counselor_chat import ChatEnabledCounselorAgent

# Import utilities
from utils.observability import ObservabilityTracker
from data.db_connector import DatabaseConnector

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleOrchestratorAgent:
    """
    Orchestrator agent that integrates existing agent implementations
    with a simple sequential workflow.
    """
    
    def __init__(self, model_name: str = "mistral"):
        """
        Initialize the orchestrator with all required agents and tools.
        
        Args:
            model_name: Name of the local Ollama model to use
        """
        self.model_name = model_name
        logger.info(f"Initializing SimpleOrchestratorAgent with model: {model_name}")
        
        # Initialize existing agents
        self.data_collector = DataCollector()
        self.validator = ValidatorAgent()
        self.assessor = AssessorAgent()
        self.counselor = ChatEnabledCounselorAgent(model_name=model_name)
        
        # Initialize database connection
        self.db_connector = DatabaseConnector()
        
        # Initialize observability
        self.observability = ObservabilityTracker()
        
    async def process_application(self, document_bytes: bytes, filename: str) -> Dict:
        """
        Process a complete application through the entire workflow.
        
        Args:
            document_bytes: Raw bytes of the uploaded document
            filename: Name of the uploaded file
            
        Returns:
            Dict containing the complete processing results
        """
        logger.info(f"Processing application: {filename}")
        
        # Initialize results dictionary
        results = {
            "application_id": None,
            "extracted_data": {},
            "validation_results": {},
            "eligibility_results": {},
            "recommendations": [],
            "explanation": {},
            "status": "processing"
        }
        
        with self.observability.start_trace("application_processing", {"filename": filename}):
            try:
                # Step 1: Data Extraction
                logger.info("Running data collector agent")
                extracted_data = await self.data_collector.process_document(document_bytes, filename)
                extracted_data['filename'] = filename
                
                results["extracted_data"] = extracted_data
                
                # Step 2: Data Validation
                logger.info("Running validator agent")
                is_valid, validation_errors = self.validator.validate(extracted_data)
                
                validation_results = {
                    "is_valid": is_valid,
                    "errors": validation_errors,
                    "validation_status": "valid" if is_valid else "invalid"
                }
                
                results["validation_results"] = validation_results
                
                # Add validation status to extracted data for assessor
                extracted_data['validation_status'] = "valid" if is_valid else "invalid"
                
                # Step 3: Eligibility Assessment (if validation passed)
                if is_valid:
                    logger.info("Running assessor agent")
                    is_eligible, reasons, assessment_details = self.assessor.assess_application(extracted_data)
                    
                    eligibility_results = {
                        "is_eligible": is_eligible,
                        "reasons": reasons,
                        "details": assessment_details,
                        "approved": is_eligible
                    }
                    
                    results["eligibility_results"] = eligibility_results
                    
                    # Step 4: Generate Recommendations
                    logger.info("Running counselor agent for recommendations")
                    application_data = {
                        **extracted_data,
                        "assessment_status": "approved" if is_eligible else "rejected",
                        "risk_level": assessment_details.get("risk_level", "medium")
                    }
                    
                    # Get recommendations using the counselor agent
                    recommendations = self.counselor._generate_recommendations(application_data)
                    explanation = self.counselor._explain_decision(application_data)
                    
                    results["recommendations"] = recommendations
                    results["explanation"] = explanation
                    
                    # Store in database if needed
                    try:
                        app_id = self.db_connector.store_application(application_data)
                        results["application_id"] = app_id
                        logger.info(f"Application stored with ID: {app_id}")
                    except Exception as e:
                        logger.error(f"Failed to store application: {str(e)}")
                
                # Update status
                results["status"] = "completed"
                return results
                
            except Exception as e:
                logger.error(f"Workflow error: {str(e)}")
                results["status"] = "error"
                results["error"] = str(e)
                return results
    
    def sync_process_application(self, document_bytes: bytes, filename: str) -> Dict:
        """
        Synchronous wrapper for process_application.
        """
        return asyncio.run(self.process_application(document_bytes, filename))
        
    def chat_with_counselor(self, application_data: Dict, user_input: str) -> str:
        """
        Enable interactive chat with the counselor agent.
        
        Args:
            application_data: Application data for context
            user_input: User's message
            
        Returns:
            Counselor's response
        """
        try:
            response = self.counselor.chat(user_input, application_data)
            return response
        except Exception as e:
            logger.error(f"Error in counselor chat: {str(e)}")
            return "I apologize, but I'm having trouble responding right now. Please try again."
