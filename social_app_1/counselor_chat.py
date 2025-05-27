"""
Extension for the CounselorAgent to add interactive chat capabilities.
This will be used by the SimpleOrchestratorAgent.
"""

import os
import logging
import json
import requests
from typing import Dict, Any, Optional, List
import time
from counselor import CounselorAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChatEnabledCounselorAgent(CounselorAgent):
    """
    Extends the CounselorAgent with interactive chat capabilities
    specifically for the SimpleOrchestratorAgent to use.
    """
    
    def __init__(self, model_name: str = "mistral"):
        """Initialize the ChatEnabledCounselorAgent."""
        super().__init__(model_name=model_name)
        self.chat_context = {}
        self.chat_history = []
        logger.info(f"ChatEnabledCounselorAgent initialized with model: {model_name}")
    
    def set_context(self, context: Dict[str, Any]):
        """Set application context for chat."""
        self.chat_context = context
        logger.info("Chat context set")
    
    def generate_initial_greeting(self) -> str:
        """Generate an initial greeting based on the context."""
        if not self.chat_context:
            return "Hello! I'm your Social Security Application assistant. How can I help you today?"
        
        status = self.chat_context.get('assessment_status', 'pending')
        if status == 'approved':
            return "Great news! Your application has been approved. I'm here to answer any questions you might have about next steps or available support programs."
        elif status == 'rejected':
            return "I see that there are some issues with your application. I'm here to help you understand the reasons and guide you on how to address them."
        else:
            return "Your application is currently being processed. I'm here to answer any questions you might have about the process or requirements."
    
    def _format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """Format application context as part of the prompt"""
        if not context:
            return ""
            
        context_str = "\n\nApplication Details:\n"
        
        # Format key details
        if "income" in context:
            context_str += f"- Income: ${context['income']:,}\n"
        if "family_size" in context:
            context_str += f"- Family Size: {context['family_size']}\n"
        if "address" in context and context["address"]:
            context_str += f"- Address: {context['address']}\n"
        if "assessment_status" in context:
            status = context["assessment_status"].capitalize()
            context_str += f"- Status: {status}\n"
        if "risk_level" in context:
            level = context["risk_level"].capitalize()
            context_str += f"- Risk Assessment: {level}\n"
            
        return context_str
    
    def _format_chat_history(self, history: List[Dict[str, str]], max_turns: int = 5) -> List[Dict[str, str]]:
        """Format the chat history for the Ollama API, keeping only recent turns"""
        # Include system message with context
        context_prompt = ""
        if self.chat_context:
            context_prompt = self._format_context_for_prompt(self.chat_context)
        
        formatted_history = [
            {
                "role": "system", 
                "content": f"You are a helpful social security application assistant. You provide guidance on applications, eligibility, and support services.{context_prompt}"
            }
        ]
        
        # Add recent chat history (last max_turns exchanges)
        if history:
            recent_history = history[-min(len(history), max_turns*2):]
            formatted_history.extend(recent_history)
            
        return formatted_history
    
    def _direct_ollama_chat(self, messages: List[Dict[str, str]]) -> str:
        """Send chat directly to Ollama API"""
        try:
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            response = requests.post(
                f"{ollama_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            if "message" in result and "content" in result["message"]:
                return result["message"]["content"]
            return "I couldn't generate a response at this time."
        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            # Try a simple fallback if API call fails
            return f"I apologize, but I encountered an issue connecting to the AI model. Error: {str(e)}"
    
    def chat(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a user message and generate a response using direct Ollama API call.
        
        Args:
            user_message: The user's message
            context: Optional application context
            
        Returns:
            Assistant's response
        """
        try:
            # Update context if provided
            if context:
                self.set_context(context)
            
            # Add user message to history
            self.chat_history.append({"role": "user", "content": user_message})
            
            # Format messages for Ollama
            messages = self._format_chat_history(self.chat_history)
            
            # Make direct API call to Ollama
            response = self._direct_ollama_chat(messages)
            
            # Add response to history
            self.chat_history.append({"role": "assistant", "content": response})
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return "I apologize, but I encountered an error while processing your request. Please try again."
