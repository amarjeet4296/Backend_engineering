from langchain_community.llms import Ollama

class LLMFactory:
    @staticmethod
    def get_llm(model_name: str = "mistral"):
        """
        Get an LLM instance from Ollama.
        
        Args:
            model_name (str): Name of the model to use (default: "mistral")
            
        Returns:
            Ollama: Configured LLM instance
        """
        return Ollama(
            model=model_name,
            temperature=0.2,  # Lower temperature for more focused responses
            num_ctx=4096,    # Context window size
            num_thread=4     # Number of threads to use
        ) 