"""
Orchestrator Agent - Master agent that coordinates all other agents in the system
using LangGraph for flow control and orchestration.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import AgentExecutor
from langchain_community.llms import Ollama
from langgraph.graph import StateGraph, END

# Load local agents
from agents.data_extraction import DataExtractionAgent
from agents.data_validation import DataValidationAgent
from agents.eligibility import EligibilityAgent
from agents.counselor import EnhancedCounselorAgent

# Load utilities
from utils.reasoning import ReActReasoning
from utils.observability import ObservabilityTracker

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    Master agent that orchestrates the workflow between various specialized agents.
    Uses LangGraph for conditional flow control and state management.
    """
    
    def __init__(self, model_name: str = "mistral"):
        """
        Initialize the orchestrator with all required agents and tools.
        
        Args:
            model_name: Name of the local Ollama model to use
        """
        self.model_name = model_name
        logger.info(f"Initializing OrchestratorAgent with model: {model_name}")
        
        # Initialize sub-agents
        self.data_extraction_agent = DataExtractionAgent()
        self.data_validation_agent = DataValidationAgent()
        self.eligibility_agent = EligibilityAgent()
        self.counselor_agent = EnhancedCounselorAgent(model_name=model_name)
        
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
        logger.info("Running data extraction agent")
        with self.observability.start_span("data_extraction"):
            result = await self.data_extraction_agent.process_document(
                state.document_bytes,
                state.filename
            )
        
        # Update state with extraction results
        state.extracted_data = result
        return state
    
    async def _run_validation_agent(self, state: "AgentState") -> "AgentState":
        """
        Run the data validation agent to validate extracted data.
        """
        logger.info("Running data validation agent")
        with self.observability.start_span("data_validation"):
            is_valid, validation_errors = self.data_validation_agent.validate(state.extracted_data)
        
        # Update state with validation results
        state.validation_results = {
            "is_valid": is_valid,
            "errors": validation_errors
        }
        return state
    
    async def _run_eligibility_agent(self, state: "AgentState") -> "AgentState":
        """
        Run the eligibility agent to assess application eligibility.
        """
        logger.info("Running eligibility assessment agent")
        with self.observability.start_span("eligibility_assessment"):
            is_eligible, reasons, assessment_details = self.eligibility_agent.assess_application(
                state.extracted_data
            )
        
        # Update state with eligibility results
        state.eligibility_results = {
            "is_eligible": is_eligible,
            "reasons": reasons,
            "details": assessment_details
        }
        return state
    
    async def _run_counselor_agent(self, state: "AgentState") -> "AgentState":
        """
        Run the counselor agent to provide guidance based on application status.
        """
        logger.info("Running counselor agent")
        with self.observability.start_span("counselor_guidance"):
            # Prepare input for counselor
            application_data = {
                **state.extracted_data,
                "validation_status": "valid" if state.validation_results.get("is_valid") else "invalid",
                "assessment_status": "approved" if state.eligibility_results.get("is_eligible", False) else "rejected",
                "risk_level": state.eligibility_results.get("details", {}).get("risk_level", "medium")
            }
            
            # Get recommendations
            recommendations = self.counselor_agent.generate_recommendations(application_data)
            
            # Get explanation
            explanation = self.counselor_agent.explain_decision(application_data)
        
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
                final_state = await self.workflow.invoke(initial_state)
                
                # Combine all results into a single dictionary
                result = {
                    "filename": filename,
                    "extracted_data": final_state.extracted_data,
                    "validation_results": final_state.validation_results,
                    "eligibility_results": final_state.eligibility_results,
                    "counselor_results": final_state.counselor_results,
                    "processing_complete": True
                }
                
                logger.info(f"Application processing complete: {filename}")
                return result
            except Exception as e:
                logger.error(f"Error processing application: {str(e)}")
                return {
                    "filename": filename,
                    "error": str(e),
                    "processing_complete": False
                }
                
    async def interactive_chat(self, user_query: str, application_data: Optional[Dict] = None) -> str:
        """
        Provide an interactive chat interface for user queries.
        
        Args:
            user_query: The user's question or request
            application_data: Optional application data for context
            
        Returns:
            Response from the counselor agent
        """
        logger.info(f"Processing interactive chat query")
        
        with self.observability.start_span("interactive_chat"):
            # Use the counselor agent to handle the query
            response = await self.counselor_agent.chat(user_query, application_data)
            
        return response


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
