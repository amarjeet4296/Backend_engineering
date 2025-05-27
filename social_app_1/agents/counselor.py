"""
Enhanced Counselor Agent - Provides personalized guidance and recommendations
through interactive chat using ReAct reasoning.
"""

import logging
import json
import os
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime
import asyncio

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.llms import Ollama

from utils.chroma_utils import ChromaManager
from utils.reasoning import ReActReasoning
from utils.observability import ObservabilityTracker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedCounselorAgent:
    """
    Enhanced counselor agent that provides personalized guidance,
    recommendations, and interactive chat capabilities.
    """
    
    def __init__(self, model_name: str = "mistral"):
        """
        Initialize the counselor agent with necessary components.
        
        Args:
            model_name: Name of the local LLM model to use
        """
        self.model_name = model_name
        self.llm = Ollama(model=model_name)
        
        # Initialize vector database
        self.chroma_manager = ChromaManager()
        
        # Initialize reasoning framework
        self.reasoning = ReActReasoning(model_name=model_name)
        
        # Initialize observability
        self.observability = ObservabilityTracker()
        
        # Create tools for the agent
        self.tools = self._create_tools()
        
        # Initialize policy documents
        self._initialize_policy_documents()
        
        logger.info(f"EnhancedCounselorAgent initialized with model: {model_name}")

    def _initialize_policy_documents(self):
        """
        Initialize policy documents in the Chroma database.
        """
        policies = [
            {
                "text": "Income Requirements: Minimum annual income of 50,000 AED for single applicants. For families, add 10,000 AED per additional family member. Income must be verifiable through pay stubs, tax returns, or bank statements.",
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
            },
            {
                "text": "Economic Enablement: Applicants may qualify for economic enablement programs including: 1) Skills training and education grants, 2) Job placement assistance, 3) Small business startup support, 4) Financial literacy programs, 5) Career counseling services. Eligibility depends on economic need and commitment to self-improvement.",
                "metadata": {"category": "enablement", "type": "guideline"}
            },
            {
                "text": "Appeals Process: Rejected applicants may appeal within 30 days by submitting: 1) Appeal form, 2) Additional supporting documentation, 3) Statement explaining special circumstances. Appeals are reviewed by a separate committee and decisions are made within 21 days of submission.",
                "metadata": {"category": "appeals", "type": "guideline"}
            }
        ]
        
        # Add policies to the vector database
        for policy in policies:
            self.chroma_manager.add_documents(
                [policy["text"]],
                [policy["metadata"]]
            )
        
        logger.info("Policy documents initialized in vector database")

    def _create_tools(self) -> List[Tool]:
        """
        Create tools for the agent to use.
        
        Returns:
            List of Tool objects
        """
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
                name="search_enablement_programs",
                func=self._search_enablement_programs,
                description="Search for relevant economic enablement programs"
            )
        ]

    def _search_policies(self, query: str) -> List[str]:
        """
        Search for relevant policy information.
        
        Args:
            query: Search query string
            
        Returns:
            List of relevant policy documents
        """
        with self.observability.start_span("search_policies"):
            results = self.chroma_manager.search_documents(query)
            return results

    def _search_enablement_programs(self, query: str) -> List[Dict]:
        """
        Search for relevant economic enablement programs.
        
        Args:
            query: Search query string
            
        Returns:
            List of relevant enablement programs
        """
        # Define available enablement programs
        programs = [
            {
                "name": "Digital Skills Training Program",
                "category": "upskilling",
                "description": "Free 12-week digital skills program covering basic IT, coding, and digital marketing",
                "eligibility": "Available to all applicants with income below 40,000 AED",
                "link": "https://example.gov/digital-skills"
            },
            {
                "name": "Government Job Placement Program",
                "category": "job_matching",
                "description": "Fast-track placement program with local employers and government agencies",
                "eligibility": "Available to all unemployed applicants",
                "link": "https://example.gov/job-placement"
            },
            {
                "name": "Financial Management Workshop",
                "category": "financial_literacy",
                "description": "Workshop series on budgeting, saving, and debt management",
                "eligibility": "Available to all applicants",
                "link": "https://example.gov/financial-workshop"
            },
            {
                "name": "Small Business Grant Program",
                "category": "business_support",
                "description": "Grants up to 50,000 AED for small business development or expansion",
                "eligibility": "Available to self-employed applicants or small business owners",
                "link": "https://example.gov/business-grants"
            },
            {
                "name": "Family Support Package",
                "category": "family_support",
                "description": "Additional benefits for large families including education subsidies and healthcare",
                "eligibility": "Available to families with 4 or more members",
                "link": "https://example.gov/family-support"
            },
            {
                "name": "Career Counseling Services",
                "category": "career_guidance",
                "description": "One-on-one career counseling and job search strategy sessions",
                "eligibility": "Available to all applicants",
                "link": "https://example.gov/career-counseling"
            },
            {
                "name": "Vocational Training Scholarships",
                "category": "education",
                "description": "Scholarships for vocational training in high-demand fields",
                "eligibility": "Available to applicants under 35 years of age",
                "link": "https://example.gov/vocational-scholarships"
            }
        ]
        
        # Simple keyword matching (in a real system, use vector search)
        query_terms = query.lower().split()
        matching_programs = []
        
        for program in programs:
            program_text = (
                program["name"].lower() + " " + 
                program["category"].lower() + " " + 
                program["description"].lower()
            )
            
            # Check if any query terms are in the program text
            if any(term in program_text for term in query_terms):
                matching_programs.append(program)
        
        # If no matches, return general programs
        if not matching_programs:
            return programs[:3]  # Return top 3 general programs
            
        return matching_programs

    def generate_recommendations(self, application_data: Dict) -> List[Dict]:
        """
        Generate recommendations based on application data.
        
        Args:
            application_data: Dictionary containing application data
            
        Returns:
            List of recommendation dictionaries
        """
        with self.observability.start_span("generate_recommendations"):
            recommendations = []
            
            # Get basic application data
            income = application_data.get("income", 0)
            family_size = application_data.get("family_size", 0)
            status = application_data.get("assessment_status", "pending")
            risk_level = application_data.get("risk_level", "medium")
            
            # Income-based recommendations
            if income < 50000:
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
            if family_size > 8:
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
            if risk_level == "high":
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
            
            # Employment recommendations
            employment_status = application_data.get("employment_status", "")
            if "unemployed" in employment_status.lower():
                recommendations.append({
                    "category": "Employment",
                    "priority": "medium",
                    "recommendation": "Being unemployed affects your eligibility. Consider exploring our job placement programs.",
                    "action_items": [
                        "Register for the Job Placement Program",
                        "Attend a career counseling session",
                        "Explore vocational training opportunities"
                    ]
                })
            
            # Financial management recommendations
            if application_data.get("liabilities", 0) > 0.4 * income:
                recommendations.append({
                    "category": "Financial Management",
                    "priority": "medium",
                    "recommendation": "Your debt-to-income ratio is high. Consider financial management resources.",
                    "action_items": [
                        "Attend a financial management workshop",
                        "Schedule a debt counseling session",
                        "Create a debt reduction plan"
                    ]
                })
            
            # Add some general recommendations if none specific
            if len(recommendations) == 0:
                recommendations.append({
                    "category": "General",
                    "priority": "low",
                    "recommendation": "Your application looks good. Here are some general resources that might be helpful.",
                    "action_items": [
                        "Explore economic enablement programs",
                        "Consider financial literacy workshops",
                        "Check eligibility for additional benefits"
                    ]
                })
            
            return recommendations

    def explain_decision(self, application_data: Dict) -> Dict:
        """
        Explain the decision and provide next steps.
        
        Args:
            application_data: Dictionary containing application data
            
        Returns:
            Dictionary with decision explanation and next steps
        """
        with self.observability.start_span("explain_decision"):
            status = application_data.get("assessment_status", "pending")
            risk_level = application_data.get("risk_level", "medium")
            
            if status == "rejected" or status == "❌ Rejected":
                return {
                    "status": "rejected",
                    "message": "Your application requires additional review.",
                    "explanation": "Based on our assessment, your application does not currently meet the eligibility criteria. This may be due to income requirements, family size considerations, or documentation issues.",
                    "next_steps": [
                        "Review the feedback provided",
                        "Address any missing requirements",
                        "Submit additional documentation if needed",
                        "Consider reapplying after addressing concerns"
                    ],
                    "timeline": "You can reapply after 30 days",
                    "appeal_option": "You have the right to appeal this decision within 30 days by submitting an appeal form and additional documentation."
                }
            elif status == "approved" or status == "✅ Approved":
                return {
                    "status": "approved",
                    "message": "Your application has been approved.",
                    "explanation": "Congratulations! Your application meets our eligibility criteria. You qualify for financial support based on your current situation.",
                    "next_steps": [
                        "Review the approval letter",
                        "Complete any remaining paperwork",
                        "Schedule a follow-up appointment if needed",
                        "Explore additional economic enablement programs"
                    ],
                    "timeline": "Next steps should be completed within 14 days",
                    "disbursement_info": "Financial support will be disbursed to your registered bank account within 7 business days."
                }
            else:
                return {
                    "status": "pending",
                    "message": "Your application is under review.",
                    "explanation": "We are currently processing your application and verifying the information provided.",
                    "next_steps": [
                        "Wait for the review process to complete",
                        "Respond to any requests for additional information",
                        "Keep your contact information up to date"
                    ],
                    "timeline": "Review process typically takes 7-10 business days",
                    "contact_info": "If you have any questions, please contact our support team at support@example.gov."
                }

    async def chat(self, query: str, application_data: Optional[Dict] = None) -> str:
        """
        Process a user query using ReAct reasoning and provide a response.
        
        Args:
            query: User's query or message
            application_data: Optional application data for context
            
        Returns:
            Response string
        """
        with self.observability.start_span("chat_interaction"):
            # Prepare context from application data if available
            context = ""
            if application_data:
                context = f"""
                Application Context:
                - Filename: {application_data.get('filename', 'Not provided')}
                - Income: {application_data.get('income', 'Not provided')} AED
                - Family Size: {application_data.get('family_size', 'Not provided')}
                - Status: {application_data.get('assessment_status', 'Not provided')}
                - Risk Level: {application_data.get('risk_level', 'Not provided')}
                """
            
            # Prepare the prompt
            prompt = f"""
            You are a helpful government social support counselor. 
            {context}
            
            Please answer the following question or request:
            {query}
            
            When responding:
            1. Be professional, clear, and supportive
            2. Reference specific policy information when relevant
            3. Provide actionable next steps when appropriate
            4. If you don't know the answer, say so and suggest where to find information
            """
            
            # Use ReAct reasoning to generate a response
            response = await self.reasoning.generate_response(prompt)
            
            # Use search tools if needed
            if any(keyword in query.lower() for keyword in ['policy', 'requirement', 'guideline', 'process']):
                policy_results = self._search_policies(query)
                if policy_results:
                    policy_info = "\n\n".join(policy_results)
                    response += f"\n\nHere are the relevant policy details:\n{policy_info}"
            
            # Use enablement search if needed
            if any(keyword in query.lower() for keyword in ['program', 'training', 'job', 'upskill', 'education', 'career']):
                program_results = self._search_enablement_programs(query)
                if program_results:
                    program_info = "\n".join([
                        f"• {p['name']}: {p['description']} - Eligibility: {p['eligibility']}"
                        for p in program_results[:3]  # Limit to 3 programs
                    ])
                    response += f"\n\nHere are some programs that might interest you:\n{program_info}"
            
            return response

    async def process_query_with_agent_executor(self, query: str, application_data: Optional[Dict] = None) -> str:
        """
        Process a user query using the LangChain agent executor.
        
        Args:
            query: User's query or message
            application_data: Optional application data for context
            
        Returns:
            Response string
        """
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful financial counselor agent that provides guidance on social support applications.
            Your role is to:
            1. Search and provide relevant policy information
            2. Generate specific recommendations based on application data
            3. Explain decisions and provide clear next steps
            4. Consider the user's query and provide targeted responses
            
            Always be professional, clear, and helpful in your responses."""),
            ("human", "{input}")
        ])
        
        # Create the agent
        agent = AgentExecutor.from_agent_and_tools(
            agent=self.llm,
            tools=self.tools,
            prompt=prompt,
            verbose=True
        )
        
        # Prepare the input
        input_text = query
        if application_data:
            input_text = f"Application data: {json.dumps(application_data)}\n\nUser query: {query}"
        
        # Run the agent
        try:
            result = await agent.ainvoke({"input": input_text})
            return result["output"]
        except Exception as e:
            logger.error(f"Error in agent execution: {str(e)}")
            return f"I apologize, but I encountered an error while processing your request. Please try again or contact support if the issue persists."
