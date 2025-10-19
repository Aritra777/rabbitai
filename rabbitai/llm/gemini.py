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
            temperature=0.25,
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
    
    @staticmethod
    def get_available_models() -> list:
        """
        Get a list of available Gemini models.

        Returns:
            List of model names
        """
        return [
            ("gemini-2.5-pro",     "Gemini 2.5 Pro – Our most advanced reasoning model"),
            ("gemini-2.5-flash",   "Gemini 2.5 Flash – High performance price-/speed-balanced model"),
            ("gemini-2.5-flash-lite", "Gemini 2.5 Flash-Lite – Most cost-efficient & fastest in the 2.5 family"),
            ("gemini-2.0-flash-001",   "Gemini 2.0 Flash – Multimodal model with next-gen features"),
        ]
