"""
Social Security Application AI Workflow Demonstration Script

This script demonstrates the complete AI workflow:
1. Document submission and data extraction
2. Data validation and checking
3. Eligibility assessment
4. Recommendation generation
5. User interaction through the counselor agent

Usage:
    python demo_workflow.py [--sample_id SAMPLE_ID] [--debug]
"""

import os
import sys
import argparse
import logging
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Import agents
from agents.orchestrator import OrchestratorAgent
from agents.data_extraction import DataExtractionAgent
from agents.data_validation import DataValidationAgent
from agents.eligibility import EligibilityAgent
from agents.counselor import CounselorAgent

# Import utilities
from utils.observability import ObservabilityTracker
from utils.reasoning import ReasoningEngine
from data.db_connector import DatabaseConnector
from data.vector_store import VectorStoreManager
from models.llm_connector import LLMConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("demo_workflow.log")
    ]
)
logger = logging.getLogger(__name__)

class WorkflowDemo:
    """
    Demonstration of the complete Social Security Application AI Workflow
    """
    
    def __init__(self, debug=False):
        """Initialize the workflow demo with all necessary components"""
        logger.info("Initializing AI Workflow Demo")
        
        # Set debug mode
        self.debug = debug
        
        # Initialize observability
        self.tracker = ObservabilityTracker(debug=debug)
        
        # Initialize LLM connector
        self.llm = LLMConnector()
        
        # Initialize reasoning engine
        self.reasoning = ReasoningEngine(llm_connector=self.llm)
        
        # Initialize database connector
        self.db = DatabaseConnector()
        
        # Initialize vector store
        self.vector_store = VectorStoreManager()
        
        # Initialize agents
        self.data_extraction = DataExtractionAgent(
            llm_connector=self.llm,
            vector_store=self.vector_store
        )
        
        self.data_validation = DataValidationAgent(
            llm_connector=self.llm,
            reasoning_engine=self.reasoning
        )
        
        self.eligibility = EligibilityAgent(
            llm_connector=self.llm,
            reasoning_engine=self.reasoning
        )
        
        self.counselor = CounselorAgent(
            llm_connector=self.llm,
            vector_store=self.vector_store
        )
        
        # Initialize orchestrator (the main workflow controller)
        self.orchestrator = OrchestratorAgent(
            data_extraction_agent=self.data_extraction,
            data_validation_agent=self.data_validation,
            eligibility_agent=self.eligibility,
            counselor_agent=self.counselor,
            db_connector=self.db,
            vector_store=self.vector_store,
            observability_tracker=self.tracker
        )
        
        logger.info("AI Workflow Demo initialization complete")
    
    def load_sample_application(self, sample_id=1):
        """Load a sample application from the synthetic data"""
        try:
            # Check if synthetic data exists
            synthetic_dir = Path("data/synthetic/output")
            app_path = synthetic_dir / "applications.csv"
            
            if not app_path.exists():
                logger.error("Synthetic data not found. Please run data/synthetic/generate_test_data.py first.")
                return None
            
            # Load applications
            applications = pd.read_csv(app_path)
            
            if sample_id > len(applications):
                logger.warning(f"Sample ID {sample_id} exceeds available samples. Using sample 1 instead.")
                sample_id = 1
            
            # Convert to 0-based index
            sample_idx = sample_id - 1
            
            # Get application data
            app_data = applications.iloc[sample_idx].to_dict()
            
            # Load documents if available
            docs_path = synthetic_dir / "documents" / f"app_{sample_id}_documents.json"
            if docs_path.exists():
                with open(docs_path, 'r') as f:
                    app_data['documents'] = json.load(f)
            
            logger.info(f"Loaded sample application {sample_id}")
            return app_data
            
        except Exception as e:
            logger.error(f"Error loading sample application: {e}")
            return None
    
    def run_workflow(self, application_data):
        """Run the complete workflow on the provided application data"""
        if not application_data:
            logger.error("No application data provided.")
            return None
        
        logger.info("Starting application workflow")
        trace_name = f"application_workflow_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Start observability trace
        with self.tracker.start_trace(trace_name, {"application_id": application_data.get("id", "unknown")}):
            try:
                # Process the application through the orchestrator
                result = self.orchestrator.process_application(application_data)
                
                # Log results
                logger.info(f"Workflow completed successfully")
                logger.info(f"Eligibility result: {result.get('eligibility_result', {}).get('approved', False)}")
                logger.info(f"Recommendations provided: {len(result.get('recommendations', []))}")
                
                return result
            
            except Exception as e:
                logger.error(f"Error in workflow: {e}")
                if self.debug:
                    import traceback
                    logger.error(traceback.format_exc())
                return {"error": str(e)}
    
    def interactive_counselor_session(self, application_data, workflow_result):
        """Run an interactive session with the counselor agent"""
        if not workflow_result:
            logger.error("No workflow result available for counselor session.")
            return
        
        print("\n" + "="*80)
        print("🤖 Interactive Counselor Session")
        print("="*80)
        print("Type 'quit' or 'exit' to end the session")
        print("-"*80)
        
        # Prepare context for the counselor
        context = {
            "application_data": application_data,
            "eligibility_result": workflow_result.get("eligibility_result", {}),
            "recommendations": workflow_result.get("recommendations", [])
        }
        
        # Initialize the counselor with the context
        self.counselor.set_context(context)
        
        # Provide an initial greeting
        initial_message = self.counselor.generate_initial_greeting()
        print(f"Counselor: {initial_message}")
        
        # Interactive loop
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Check for exit command
            if user_input.lower() in ['quit', 'exit']:
                print("\nCounselor: Thank you for using our service. Goodbye!")
                break
            
            # Process the message through the counselor
            with self.tracker.start_trace("counselor_interaction", {"query": user_input}):
                try:
                    response = self.counselor.chat(user_input)
                    print(f"\nCounselor: {response}")
                except Exception as e:
                    logger.error(f"Error in counselor chat: {e}")
                    print("\nCounselor: I apologize, but I'm having trouble responding right now. Please try again.")

def main():
    """Main entry point for the demo script"""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Social Security Application AI Workflow Demo")
    parser.add_argument("--sample_id", type=int, default=1, help="ID of the sample application to use")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Set log level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize demo
    demo = WorkflowDemo(debug=args.debug)
    
    # Load sample application
    app_data = demo.load_sample_application(args.sample_id)
    
    if not app_data:
        print("Could not load sample application. Exiting.")
        return
    
    # Print application summary
    print("\n" + "="*80)
    print("📄 Sample Application Summary")
    print("="*80)
    print(f"Name: {app_data.get('first_name', '')} {app_data.get('last_name', '')}")
    print(f"Age: {app_data.get('age', '')}")
    print(f"Income: {app_data.get('income', '')}")
    print(f"Family Size: {app_data.get('family_size', '')}")
    print(f"Address: {app_data.get('address', '')}")
    print("="*80 + "\n")
    
    # Run workflow
    print("Running application workflow...")
    result = demo.run_workflow(app_data)
    
    if not result or "error" in result:
        print(f"Workflow failed: {result.get('error', 'Unknown error')}")
        return
    
    # Print workflow results
    print("\n" + "="*80)
    print("🔍 Workflow Results")
    print("="*80)
    
    # Eligibility
    eligibility = result.get("eligibility_result", {})
    approved = eligibility.get("approved", False)
    
    print(f"Application {'Approved' if approved else 'Not Approved'}")
    
    if "reasons" in eligibility:
        print("\nReasons:")
        for reason in eligibility["reasons"]:
            print(f"- {reason}")
    
    # Recommendations
    recommendations = result.get("recommendations", [])
    if recommendations:
        print("\nRecommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec.get('title', 'Recommendation')}")
            print(f"   {rec.get('description', '')}")
            print()
    
    print("="*80 + "\n")
    
    # Start interactive counselor session
    demo.interactive_counselor_session(app_data, result)

if __name__ == "__main__":
    main()
