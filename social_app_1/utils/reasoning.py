"""
Reasoning utilities for the AI workflow.
Implements ReAct (Reasoning and Acting) and other reasoning frameworks.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage, AIMessage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReActReasoning:
    """
    Implementation of the ReAct (Reasoning and Acting) framework for improved
    reasoning capabilities in LLM-based agents.
    """
    
    def __init__(self, model_name: str = "mistral"):
        """
        Initialize the ReAct reasoning framework.
        
        Args:
            model_name: Name of the local LLM model to use
        """
        self.model_name = model_name
        self.llm = Ollama(model=model_name)
        logger.info(f"ReActReasoning initialized with model: {model_name}")

    async def generate_response(self, prompt: str, max_iterations: int = 3) -> str:
        """
        Generate a response using the ReAct framework with iterative reasoning.
        
        Args:
            prompt: The input prompt
            max_iterations: Maximum number of reasoning iterations
            
        Returns:
            Final response string
        """
        # Initial thought process
        react_prompt = f"""
        {prompt}
        
        Let's approach this step by step:
        
        1. Thought: Think about what information is needed to answer this query correctly.
        2. Action: Determine what actions to take based on the available information.
        3. Observation: What additional information would help improve the response?
        4. Response: Based on thoughts and observations, formulate a helpful response.
        """
        
        # First iteration
        response = self.llm.invoke(react_prompt)
        
        # Parse the response to extract the reasoning process
        thoughts, actions, observations, final_response = self._parse_react_output(response)
        
        # If we already have a final response section, return it
        if final_response:
            return final_response
        
        # Additional iterations if needed
        current_context = f"""
        {prompt}
        
        Initial thoughts: {thoughts}
        Initial actions: {actions}
        Initial observations: {observations}
        
        Let's refine our thinking:
        
        1. Additional thoughts: What more should be considered?
        2. Refined actions: What specific actions are needed based on all information?
        3. Final observations: What conclusions can be drawn?
        4. Final response: Provide a comprehensive, helpful response.
        """
        
        # Final iteration
        refined_response = self.llm.invoke(current_context)
        
        # Extract the final response
        _, _, _, final_response = self._parse_react_output(refined_response)
        
        # If we still don't have a clear final response, extract the most useful part
        if not final_response:
            final_response = self._extract_best_response(refined_response)
        
        return final_response

    def _parse_react_output(self, text: str) -> tuple:
        """
        Parse the output from the ReAct reasoning process.
        
        Args:
            text: The raw output text from the LLM
            
        Returns:
            Tuple of (thoughts, actions, observations, final_response)
        """
        thoughts = ""
        actions = ""
        observations = ""
        final_response = ""
        
        # Extract sections based on keywords
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Identify sections
            if "thought:" in line.lower() or "thinking:" in line.lower():
                current_section = "thoughts"
                thoughts += line + "\n"
            elif "action:" in line.lower():
                current_section = "actions"
                actions += line + "\n"
            elif "observation:" in line.lower():
                current_section = "observations"
                observations += line + "\n"
            elif "response:" in line.lower() or "final response:" in line.lower():
                current_section = "final_response"
                final_response = ""  # Reset to capture everything after this marker
            elif current_section == "final_response" and line:
                final_response += line + "\n"
            elif current_section and line:
                # Add to current section
                if current_section == "thoughts":
                    thoughts += line + "\n"
                elif current_section == "actions":
                    actions += line + "\n"
                elif current_section == "observations":
                    observations += line + "\n"
        
        # Clean up the final response
        if not final_response:
            # If no explicit final response section, look for content after "Based on"
            for line in lines:
                if "based on" in line.lower() and len(line) > 20:
                    final_response = line + "\n"
                    # Also include subsequent lines
                    start_collecting = True
                    for follow_line in lines[lines.index(line)+1:]:
                        if start_collecting:
                            final_response += follow_line + "\n"
                    break
        
        return thoughts.strip(), actions.strip(), observations.strip(), final_response.strip()

    def _extract_best_response(self, text: str) -> str:
        """
        Extract the most useful response content when structured parsing fails.
        
        Args:
            text: The raw output text from the LLM
            
        Returns:
            Best response string
        """
        # Look for paragraphs that seem to be direct responses
        paragraphs = text.split('\n\n')
        
        # Filter out obvious non-response paragraphs
        response_paragraphs = []
        for paragraph in paragraphs:
            # Skip short paragraphs
            if len(paragraph) < 20:
                continue
                
            # Skip paragraphs that start with obvious thinking markers
            if any(paragraph.lower().startswith(marker) for marker in [
                "thought", "thinking", "let me", "i need to", "action:", "observation:"
            ]):
                continue
                
            # Keep paragraphs that seem like responses
            response_paragraphs.append(paragraph)
        
        # If we found response paragraphs, combine them
        if response_paragraphs:
            return "\n\n".join(response_paragraphs)
            
        # Otherwise, use the last substantial paragraph as a fallback
        substantial_paragraphs = [p for p in paragraphs if len(p) > 50]
        if substantial_paragraphs:
            return substantial_paragraphs[-1]
            
        # Last resort: return the original text with minimal cleanup
        return text.replace("Thought:", "").replace("Action:", "").replace("Observation:", "")


class ReflexionReasoning:
    """
    Implementation of the Reflexion reasoning framework, which extends ReAct
    with self-reflection capabilities for improved problem-solving.
    """
    
    def __init__(self, model_name: str = "mistral"):
        """
        Initialize the Reflexion reasoning framework.
        
        Args:
            model_name: Name of the local LLM model to use
        """
        self.model_name = model_name
        self.llm = Ollama(model=model_name)
        self.conversation_history = []
        logger.info(f"ReflexionReasoning initialized with model: {model_name}")

    async def generate_response(self, prompt: str, reflection_iterations: int = 1) -> str:
        """
        Generate a response using the Reflexion framework with self-reflection.
        
        Args:
            prompt: The input prompt
            reflection_iterations: Number of self-reflection iterations
            
        Returns:
            Final response string
        """
        # Add prompt to conversation history
        self.conversation_history.append(HumanMessage(content=prompt))
        
        # Initial response
        initial_prompt = f"""
        {prompt}
        
        Please respond to this request. First, think through the problem step by step.
        """
        
        response = self.llm.invoke(initial_prompt)
        self.conversation_history.append(AIMessage(content=response))
        
        # Iterate through reflection cycles
        for i in range(reflection_iterations):
            # Generate self-reflection
            reflection_prompt = f"""
            I want you to reflect on your previous response:
            
            {response}
            
            Please identify:
            1. Any incorrect assumptions you made
            2. Any logical errors in your reasoning
            3. Any additional information that would be helpful
            4. How you could improve your response
            
            Focus on making your response more accurate, comprehensive, and helpful.
            """
            
            reflection = self.llm.invoke(reflection_prompt)
            
            # Generate improved response based on reflection
            improved_prompt = f"""
            Original request: {prompt}
            
            Your previous response: {response}
            
            Your self-reflection: {reflection}
            
            Based on this reflection, please provide an improved response that addresses the issues you identified.
            """
            
            response = self.llm.invoke(improved_prompt)
            self.conversation_history.append(AIMessage(content=response))
        
        return response


class PlanAndSolveReasoning:
    """
    Implementation of the Plan-and-Solve (PaS) reasoning framework for breaking down
    complex problems into manageable steps.
    """
    
    def __init__(self, model_name: str = "mistral"):
        """
        Initialize the Plan-and-Solve reasoning framework.
        
        Args:
            model_name: Name of the local LLM model to use
        """
        self.model_name = model_name
        self.llm = Ollama(model=model_name)
        logger.info(f"PlanAndSolveReasoning initialized with model: {model_name}")

    async def generate_response(self, prompt: str, max_steps: int = 5) -> str:
        """
        Generate a response using the Plan-and-Solve framework.
        
        Args:
            prompt: The input prompt
            max_steps: Maximum number of steps in the plan
            
        Returns:
            Final response string
        """
        # Generate a plan
        plan_prompt = f"""
        {prompt}
        
        Let's approach this methodically by creating a plan:
        
        1. First, identify the key aspects of the problem.
        2. Break down the problem into {max_steps} or fewer clear steps.
        3. For each step, briefly describe what needs to be done.
        
        Please provide a clear, step-by-step plan to address this request.
        """
        
        plan = self.llm.invoke(plan_prompt)
        
        # Execute the plan
        execute_prompt = f"""
        Original request: {prompt}
        
        Plan:
        {plan}
        
        Now, let's execute this plan step by step and provide a comprehensive response.
        For each step:
        1. Explain your reasoning
        2. Show your work
        3. State your conclusion
        
        Finally, synthesize all steps into a cohesive final response.
        """
        
        execution = self.llm.invoke(execute_prompt)
        
        # Extract final answer
        final_prompt = f"""
        Original request: {prompt}
        
        Plan: {plan}
        
        Execution of plan: {execution}
        
        Based on the above work, provide a clear, concise final response that directly addresses the original request.
        Focus on clarity and actionable information. Remove any unnecessary thinking or intermediate steps from your final response.
        """
        
        final_response = self.llm.invoke(final_prompt)
        
        return final_response
