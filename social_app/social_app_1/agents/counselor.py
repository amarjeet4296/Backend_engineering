from typing import Dict, List, Optional, Tuple
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from langchain_community.llms import Ollama

from utils.ollama_utils import LLMFactory
from utils.chroma_utils import ChromaManager
from assessor import AssessorAgent

# Load environment variables
load_dotenv()

class CounselorAgent:
    def __init__(self, model_name: str = "mistral"):
        """Initialize the CounselorAgent with necessary components."""
        self.model_name = model_name
        self.chroma_manager = ChromaManager()
        self.assessor = AssessorAgent()
        self.tools = self._create_tools()
        self.agent = self._create_agent()
        self._initialize_policy_documents()

    def _initialize_policy_documents(self):
        """Initialize policy documents in the Chroma database."""
        policies = [
            {
                "text": "Income Requirements: Minimum annual income of $50,000 for single applicants. For families, add $10,000 per additional family member. Income must be verifiable through pay stubs, tax returns, or bank statements.",
                "metadata": {"category": "income", "type": "requirement"}
            },
            {
                "text": "Family Size Guidelines: Maximum family size of 8 members. Each additional family member must be documented with birth certificates or legal guardianship papers. Special circumstances may be considered with additional documentation.",
                "metadata": {"category": "family", "type": "guideline"}
            },
            {
                "text": "Required Documents: 1) Valid government-issued ID, 2) Proof of income (last 3 months), 3) Proof of residence (utility bills or lease), 4) Family documentation (birth certificates), 5) Employment verification letter. All documents must be current and notarized if required.",
                "metadata": {"category": "documents", "type": "requirement"}
            },
            {
                "text": "Application Process: 1) Submit initial application with basic information, 2) Provide required documentation within 30 days, 3) Undergo verification process (7-10 business days), 4) Receive decision within 15 business days. Rejected applications can be appealed within 30 days with additional documentation.",
                "metadata": {"category": "process", "type": "guideline"}
            },
            {
                "text": "Risk Assessment: Applications are evaluated based on income stability, family size, and documentation completeness. High-risk factors include: income below requirements, incomplete documentation, or family size exceeding guidelines. Mitigation strategies must be provided for high-risk applications.",
                "metadata": {"category": "risk", "type": "guideline"}
            }
        ]
        
        for policy in policies:
            self.chroma_manager.add_documents(
                [policy["text"]],
                [policy["metadata"]]
            )

    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent to use."""
        return [
            Tool(
                name="search_policies",
                func=self._search_policies,
                description="Search for relevant policy information"
            ),
            Tool(
                name="generate_recommendations",
                func=self._generate_recommendations,
                description="Generate recommendations based on application data"
            ),
            Tool(
                name="explain_decision",
                func=self._explain_decision,
                description="Explain the decision and provide next steps"
            ),
            Tool(
                name="get_assessment_history",
                func=self._get_assessment_history,
                description="Get recent assessment history"
            )
        ]

    def _create_agent(self) -> AgentExecutor:
        """Create the agent executor with a chat prompt template."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful financial counselor agent that provides guidance on applications.
            Your role is to:
            1. Search and provide relevant policy information
            2. Generate specific recommendations based on application data
            3. Explain decisions and provide clear next steps
            4. Consider the user's query and provide targeted responses
            
            Always be professional, clear, and helpful in your responses."""),
            ("human", "{input}")
        ])
        
        return AgentExecutor.from_agent_and_tools(
            agent=Ollama(model=self.model_name),
            tools=self.tools,
            prompt=prompt,
            verbose=True
        )

    def _search_policies(self, query: str) -> List[str]:
        """Search for relevant policy information."""
        results = self.chroma_manager.search_documents("policies", query)
        return results

    def _generate_recommendations(self, application_data: Dict) -> List[Dict]:
        """Generate recommendations based on application data."""
        recommendations = []
        
        # Income-based recommendations
        if application_data.get("income", 0) < 50000:
            recommendations.append({
                "category": "Income",
                "priority": "high",
                "recommendation": "Your income is below the minimum requirement. Consider providing additional income documentation or proof of supplementary income sources.",
                "action_items": [
                    "Submit recent payslips",
                    "Provide bank statements",
                    "Include any additional income sources"
                ]
            })
        
        # Family size recommendations
        if application_data.get("family_size", 0) > 8:
            recommendations.append({
                "category": "Family Size",
                "priority": "high",
                "recommendation": "Your family size exceeds the maximum limit. Please provide documentation for special circumstances.",
                "action_items": [
                    "Submit birth certificates for all family members",
                    "Provide proof of relationship",
                    "Include special circumstances documentation"
                ]
            })
        
        # Risk mitigation recommendations
        if application_data.get("risk_level") == "high":
            recommendations.append({
                "category": "Risk Mitigation",
                "priority": "high",
                "recommendation": "Your application has been flagged as high risk. Additional documentation is required.",
                "action_items": [
                    "Submit additional proof of residence",
                    "Provide employment verification",
                    "Include any relevant supporting documents"
                ]
            })
        
        return recommendations

    def _explain_decision(self, application_data: Dict) -> Dict:
        """Explain the decision and provide next steps."""
        status = application_data.get("assessment_status", "pending")
        risk_level = application_data.get("risk_level", "medium")
        
        if status == "rejected":
            return {
                "status": status,
                "message": "Your application requires additional review.",
                "next_steps": [
                    "Review the feedback provided",
                    "Address any missing requirements",
                    "Submit additional documentation if needed",
                    "Consider reapplying after addressing concerns"
                ],
                "timeline": "You can reapply after 30 days"
            }
        elif status == "approved":
            return {
                "status": status,
                "message": "Your application has been approved.",
                "next_steps": [
                    "Review the approval letter",
                    "Complete any remaining paperwork",
                    "Schedule a follow-up appointment if needed"
                ],
                "timeline": "Next steps should be completed within 14 days"
            }
        else:
            return {
                "status": status,
                "message": "Your application is under review.",
                "next_steps": [
                    "Wait for the review process to complete",
                    "Respond to any requests for additional information",
                    "Keep your contact information up to date"
                ],
                "timeline": "Review process typically takes 7-10 business days"
            }

    def _get_assessment_history(self, application_data: Dict) -> List[Dict]:
        """Get recent assessment history."""
        # This would typically query a database
        return []

    def provide_guidance(self, application_data: Dict, query: Optional[str] = None) -> Dict:
        """Provide comprehensive guidance based on application data and optional query."""
        try:
            # Search for relevant policies
            policy_info = self._search_policies(query) if query else []
            
            # Generate recommendations
            recommendations = self._generate_recommendations(application_data)
            
            # Get decision explanation
            explanation = self._explain_decision(application_data)
            
            # Get assessment history
            history = self._get_assessment_history(application_data)
            
            return {
                "status": "success",
                "recommendations": recommendations,
                "explanation": explanation,
                "policy_info": policy_info,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def __del__(self):
        """Cleanup when the agent is destroyed"""
        try:
            # Close any open connections
            pass
        except:
            pass


if __name__ == "__main__":
    # Example usage
    counselor = CounselorAgent()
    guidance = counselor.provide_guidance(
        application_data={
            "income": 45000,
            "family_size": 6,
            "assessment_status": "rejected",
            "risk_level": "high"
        },
        query="What are the income requirements?"
    )
    print(json.dumps(guidance, indent=2)) 