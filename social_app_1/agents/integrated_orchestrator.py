"""
Integrated Orchestrator Agent - Coordinates the workflow between existing agents
while maintaining enhanced functionality with LangGraph for flow control.
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

# Import existing agents
from data_collector import DataCollector
from validator import ValidatorAgent
from assessor import AssessorAgent
from counselor import CounselorAgent

# Import utilities
from utils.observability import ObservabilityTracker
from utils.reasoning import ReActReasoning
from data.db_connector import DatabaseConnector
from data.vector_store import VectorStoreManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegratedOrchestratorAgent:
    """
    Orchestrator agent that integrates existing agent implementations
    with enhanced workflow management and reasoning capabilities.
    """
    
    def __init__(self, model_name: str = "mistral"):
        """
        Initialize the orchestrator with all required agents and tools.
        
        Args:
            model_name: Name of the local Ollama model to use
        """
        self.model_name = model_name
        logger.info(f"Initializing IntegratedOrchestratorAgent with model: {model_name}")
        
        # Initialize existing agents
        self.data_collector = DataCollector()
        self.validator = ValidatorAgent()
        self.assessor = AssessorAgent()
        self.counselor = CounselorAgent(model_name=model_name)
        
        # Initialize database and vector store connections
        self.db_connector = DatabaseConnector()
        self.vector_store = VectorStoreManager()
        
        # Initialize reasoning framework
        self.reasoning = ReActReasoning(model_name=model_name)
        
        # Initialize observability
        self.observability = ObservabilityTracker()
        
        # Build the agent graph
        self.workflow = self._build_workflow_graph()
        
    def _build_workflow_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow for the application processing pipeline.
        """
        # Define the workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("extract", self._run_extraction_agent)
        workflow.add_node("validate", self._run_validation_agent)
        workflow.add_node("assess_eligibility", self._run_eligibility_agent)
        workflow.add_node("provide_guidance", self._run_counselor_agent)
        
        # Define the edges (transitions between agents)
        workflow.add_edge("extract", "validate")
        workflow.add_conditional_edges(
            "validate",
            self._validation_router,
            {
                "valid": "assess_eligibility",
                "invalid": "provide_guidance"
            }
        )
        workflow.add_conditional_edges(
            "assess_eligibility",
            self._eligibility_router,
            {
                "eligible": "provide_guidance",
                "ineligible": "provide_guidance"
            }
        )
        workflow.add_edge("provide_guidance", END)
        
        # Set the entry point
        workflow.set_entry_point("extract")
        
        return workflow.compile()
    
    def _validation_router(self, state: "AgentState") -> str:
        """
        Route based on validation results.
        """
        return "valid" if state.validation_results.get("is_valid", False) else "invalid"
    
    def _eligibility_router(self, state: "AgentState") -> str:
        """
        Route based on eligibility results.
        """
        return "eligible" if state.eligibility_results.get("is_eligible", False) else "ineligible"
    
    async def _run_extraction_agent(self, state: "AgentState") -> "AgentState":
        """
        Run the data extraction agent to process documents.
        """
        logger.info("Running data collector agent")
        with self.observability.start_span("data_extraction"):
            # The original data_collector uses async
            result = await self.data_collector.process_document(
                state.document_bytes,
                state.filename
            )
        
        # Add filename to the extracted data
        result['filename'] = state.filename
        
        # Update state with extraction results
        state.extracted_data = result
        return state
    
    def _run_validation_agent(self, state: "AgentState") -> "AgentState":
        """
        Run the validation agent to validate extracted data.
        """
        logger.info("Running validator agent")
        with self.observability.start_span("data_validation"):
            is_valid, validation_errors = self.validator.validate(state.extracted_data)
        
        # Update state with validation results
        state.validation_results = {
            "is_valid": is_valid,
            "errors": validation_errors,
            "validation_status": "valid" if is_valid else "invalid"
        }
        
        # Add validation status to extracted data for assessor
        state.extracted_data['validation_status'] = "valid" if is_valid else "invalid"
        
        return state
    
    def _run_eligibility_agent(self, state: "AgentState") -> "AgentState":
        """
        Run the eligibility agent to assess application eligibility.
        """
        logger.info("Running assessor agent")
        with self.observability.start_span("eligibility_assessment"):
            is_eligible, reasons, assessment_details = self.assessor.assess_application(
                state.extracted_data
            )
        
        # Update state with eligibility results
        state.eligibility_results = {
            "is_eligible": is_eligible,
            "reasons": reasons,
            "details": assessment_details,
            "approved": is_eligible  # Match the existing assessor's terminology
        }
        return state
    
    def _run_counselor_agent(self, state: "AgentState") -> "AgentState":
        """
        Run the counselor agent to provide guidance based on application status.
        """
        logger.info("Running counselor agent")
        with self.observability.start_span("counselor_guidance"):
            # Prepare input for counselor
            application_data = {
                **state.extracted_data,
                "validation_status": state.validation_results.get("validation_status", "invalid"),
                "assessment_status": "approved" if state.eligibility_results.get("is_eligible", False) else "rejected",
                "risk_level": state.eligibility_results.get("details", {}).get("risk_level", "medium")
            }
            
            # Get recommendations using the original counselor's methods
            recommendations = self.counselor._generate_recommendations(application_data)
            
            # Get explanation
            explanation = self.counselor._explain_decision(application_data)
        
        # Update state with counselor results
        state.counselor_results = {
            "recommendations": recommendations,
            "explanation": explanation
        }
        return state
    
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
        
        # Create initial state
        initial_state = AgentState(
            document_bytes=document_bytes,
            filename=filename
        )
        
        # Run the workflow
        with self.observability.start_trace("application_processing", {"filename": filename}):
            try:
                # Execute the workflow
                final_state = await self.workflow.ainvoke(initial_state)
                
                # Prepare results
                results = {
                    "application_id": None,  # Will be filled if saved to DB
                    "extracted_data": final_state.extracted_data,
                    "validation_results": final_state.validation_results,
                    "eligibility_results": final_state.eligibility_results,
                    "recommendations": final_state.counselor_results.get("recommendations", []),
                    "explanation": final_state.counselor_results.get("explanation", {}),
                    "status": "completed"
                }
                
                # Store in database if validated
                if final_state.validation_results.get("is_valid", False):
                    try:
                        app_id = self.db_connector.store_application({
                            **final_state.extracted_data,
                            "assessment_status": "approved" if final_state.eligibility_results.get("is_eligible", False) else "rejected",
                            "risk_level": final_state.eligibility_results.get("details", {}).get("risk_level", "medium"),
                            "recommendations": final_state.counselor_results.get("recommendations", []),
                        })
                        results["application_id"] = app_id
                        logger.info(f"Application stored with ID: {app_id}")
                    except Exception as e:
                        logger.error(f"Failed to store application: {str(e)}")
                
                return results
                
            except Exception as e:
                logger.error(f"Workflow error: {str(e)}")
                return {
                    "status": "error",
                    "error": str(e)
                }
                
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
            with self.observability.start_span("counselor_chat"):
                response = self.counselor.chat(user_input, application_data)
            return response
        except Exception as e:
            logger.error(f"Error in counselor chat: {str(e)}")
            return "I apologize, but I'm having trouble responding right now. Please try again."

    def sync_process_application(self, document_bytes: bytes, filename: str) -> Dict:
        """
        Synchronous wrapper for process_application.
        """
        return asyncio.run(self.process_application(document_bytes, filename))


class AgentState:
    """
    State container for the agent workflow.
    """
    def __init__(
            self,
            document_bytes: bytes = None,
            filename: str = None,
            extracted_data: Dict = None,
            validation_results: Dict = None,
            eligibility_results: Dict = None,
            counselor_results: Dict = None
        ):
        self.document_bytes = document_bytes
        self.filename = filename
        self.extracted_data = extracted_data or {}
        self.validation_results = validation_results or {}
        self.eligibility_results = eligibility_results or {}
        self.counselor_results = counselor_results or {}
