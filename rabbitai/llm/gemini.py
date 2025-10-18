"""Gemini LLM integration for RabbitAI"""

from langchain_google_genai import ChatGoogleGenerativeAI
from .base import BaseLLM


class GeminiLLM(BaseLLM):
    """Google Gemini LLM implementation"""

    def __init__(self, api_key: str, model: str = "gemini-pro"):
        """
        Initialize Gemini LLM.

        Args:
            api_key: Google API key for Gemini
            model: Model name (default: gemini-pro)
        """
        self.model_name = model
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.1,  # Low temperature for more deterministic responses
            convert_system_message_to_human=True  # Gemini compatibility
        )

    def invoke(self, prompt: str):
        """
        Send a prompt to Gemini and get a response.

        Args:
            prompt: The prompt string

        Returns:
            LangChain message response object
        """
        return self.llm.invoke(prompt)

    def is_available(self) -> bool:
        """
        Check if Gemini is available and configured correctly.

        Returns:
            True if Gemini can be used, False otherwise
        """
        try:
            # Test with a simple query
            response = self.llm.invoke("Hello")
            return response is not None
        except Exception as e:
            print(f"Gemini availability check failed: {e}")
            return False

    def get_model_name(self) -> str:
        """Get the Gemini model name"""
        return self.model_name
