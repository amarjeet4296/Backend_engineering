"""
LLM Connector - Manages interactions with local LLM models via Ollama.
Provides unified interface for text generation, embeddings, and model management.
"""

import logging
import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union
import requests
from dotenv import load_dotenv
from langchain_community.llms import Ollama

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMConnector:
    """
    Manages interactions with local large language models via Ollama.
    Provides a unified interface for text generation, embeddings, and model management.
    """
    
    def __init__(self, default_model: str = "mistral"):
        """
        Initialize the LLM connector with the specified default model.
        
        Args:
            default_model: Name of the default model to use
        """
        self.default_model = default_model
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.available_models = self._get_available_models()
        
        # Initialize LangChain Ollama client
        self.llm = Ollama(
            model=default_model,
            temperature=0.2,
            num_ctx=4096,
            num_thread=4
        )
        
        logger.info(f"LLMConnector initialized with default model: {default_model}")
        
        # If default model is not available, warn and suggest downloading
        if default_model not in self.available_models:
            logger.warning(f"Default model '{default_model}' not available locally")
            logger.info(f"Available models: {', '.join(self.available_models)}")
            logger.info(f"To download the default model, run: ollama pull {default_model}")

    def _get_available_models(self) -> List[str]:
        """
        Get a list of available models from Ollama.
        
        Returns:
            List of available model names
        """
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                models_data = response.json()
                return [model["name"] for model in models_data.get("models", [])]
            else:
                logger.error(f"Failed to get models: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting available models: {str(e)}")
            return []

    def list_models(self) -> List[Dict[str, Any]]:
        """
        Get detailed information about available models.
        
        Returns:
            List of model dictionaries with details
        """
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                return response.json().get("models", [])
            else:
                logger.error(f"Failed to list models: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []

    def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama repository.
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Pulling model: {model_name}")
            response = requests.post(
                f"{self.ollama_base_url}/api/pull",
                json={"name": model_name}
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully pulled model: {model_name}")
                # Update available models
                self.available_models = self._get_available_models()
                return True
            else:
                logger.error(f"Failed to pull model: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error pulling model: {str(e)}")
            return False

    def generate_text(self, prompt: str, model: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 1024) -> str:
        """
        Generate text using the specified model.
        
        Args:
            prompt: Input prompt
            model: Model to use (defaults to the default model)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text
        """
        model_name = model or self.default_model
        
        try:
            # Check if model is available
            if model_name not in self.available_models:
                logger.warning(f"Model '{model_name}' not available, attempting to pull")
                success = self.pull_model(model_name)
                if not success:
                    logger.warning(f"Falling back to default model: {self.default_model}")
                    model_name = self.default_model
            
            # Use LangChain Ollama client
            ollama_instance = Ollama(
                model=model_name,
                temperature=temperature,
                num_ctx=4096,
                num_thread=4
            )
            
            response = ollama_instance.invoke(prompt)
            return response
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return f"Error generating text: {str(e)}"

    async def generate_text_async(self, prompt: str, model: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 1024) -> str:
        """
        Generate text asynchronously using the specified model.
        
        Args:
            prompt: Input prompt
            model: Model to use (defaults to the default model)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text
        """
        # Run in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.generate_text(prompt, model, temperature, max_tokens)
        )

    def generate_embeddings(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """
        Generate embeddings for the given texts.
        
        Args:
            texts: List of input texts
            model: Model to use (defaults to the default model)
            
        Returns:
            List of embedding vectors
        """
        model_name = model or self.default_model
        
        try:
            embeddings = []
            for text in texts:
                response = requests.post(
                    f"{self.ollama_base_url}/api/embeddings",
                    json={"model": model_name, "prompt": text}
                )
                
                if response.status_code == 200:
                    embedding = response.json().get("embedding", [])
                    embeddings.append(embedding)
                else:
                    logger.error(f"Failed to generate embedding: {response.status_code} - {response.text}")
                    # Add empty embedding as placeholder
                    embeddings.append([0.0] * 384)  # Common embedding size
            
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return [[0.0] * 384 for _ in texts]  # Return empty embeddings

    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.2) -> Dict[str, Any]:
        """
        Generate a chat completion using the specified model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (defaults to the default model)
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Chat completion response
        """
        model_name = model or self.default_model
        
        try:
            # Format messages for Ollama
            prompt = ""
            for message in messages:
                role = message["role"]
                content = message["content"]
                
                if role == "system":
                    prompt += f"<s>[INST] <<SYS>>\n{content}\n<</SYS>>\n\n"
                elif role == "user":
                    if prompt:
                        prompt += f"{content} [/INST]"
                    else:
                        prompt += f"[INST] {content} [/INST]"
                elif role == "assistant":
                    prompt += f" {content} </s><s>"
            
            # Generate response
            response = requests.post(
                f"{self.ollama_base_url}/api/chat",
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to generate chat completion: {response.status_code} - {response.text}")
                return {
                    "message": {"role": "assistant", "content": "Error generating response"},
                    "error": f"Status code: {response.status_code}"
                }
        except Exception as e:
            logger.error(f"Error generating chat completion: {str(e)}")
            return {
                "message": {"role": "assistant", "content": f"Error: {str(e)}"},
                "error": str(e)
            }

    async def chat_completion_async(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.2) -> Dict[str, Any]:
        """
        Generate a chat completion asynchronously using the specified model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (defaults to the default model)
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Chat completion response
        """
        # Run in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.chat_completion(messages, model, temperature)
        )

    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model_name: Name of the model (defaults to the default model)
            
        Returns:
            Dictionary with model information
        """
        model = model_name or self.default_model
        
        try:
            models = self.list_models()
            for model_info in models:
                if model_info.get("name") == model:
                    return model_info
            
            return {"name": model, "error": "Model not found"}
        except Exception as e:
            logger.error(f"Error getting model info: {str(e)}")
            return {"name": model, "error": str(e)}

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in the given text.
        This is a rough estimate based on character count.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token for English text
        return len(text) // 4
