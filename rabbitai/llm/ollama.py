"""Ollama LLM integration for RabbitAI"""

from langchain_community.chat_models import ChatOllama
from .base import BaseLLM
import subprocess
from typing import List


class OllamaLLM(BaseLLM):
    """Ollama local LLM implementation"""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama LLM.

        Args:
            model: Model name (e.g., llama3, codellama, mistral)
            base_url: Ollama server URL (default: http://localhost:11434)
        """
        self.model_name = model
        self.base_url = base_url
        self.llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=0.1  # Low temperature for more deterministic responses
        )

    def invoke(self, prompt: str):
        """
        Send a prompt to Ollama and get a response.

        Args:
            prompt: The prompt string

        Returns:
            LangChain message response object
        """
        return self.llm.invoke(prompt)

    def is_available(self) -> bool:
        """
        Check if Ollama is available and the model is accessible.

        Returns:
            True if Ollama can be used, False otherwise
        """
        try:
            # Test with a simple query
            response = self.llm.invoke("Hello")
            return response is not None
        except Exception as e:
            print(f"Ollama availability check failed: {e}")
            print(f"Make sure Ollama is running: ollama serve")
            print(f"And the model '{self.model_name}' is installed: ollama pull {self.model_name}")
            return False

    def get_model_name(self) -> str:
        """Get the Ollama model name"""
        return self.model_name
    
    @staticmethod
    def get_available_models() -> List[str]:
        """Fetch available Ollama models from local system"""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return []

            # Parse output to extract model names
            # Format: NAME                    ID              SIZE      MODIFIED
            models = []
            lines = result.stdout.strip().split('\n')

            # Skip header line
            for line in lines[1:]:
                if line.strip():
                    # Extract first column (model name)
                    parts = line.split()
                    if parts:
                        model_name = parts[0]
                        # Remove :latest or other tags if present
                        base_name = model_name
                        if base_name not in models:
                            models.append(base_name)

            return models
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # Ollama not installed or not running
            return []
