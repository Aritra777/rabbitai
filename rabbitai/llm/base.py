"""Base LLM interface for RabbitAI"""

from abc import ABC, abstractmethod
from typing import Any


class BaseLLM(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    def invoke(self, prompt: str) -> Any:
        """
        Send a prompt to the LLM and get a response.

        Args:
            prompt: The prompt string to send

        Returns:
            Response object from the LLM (implementation-specific)
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the LLM is available and configured correctly.

        Returns:
            True if LLM can be used, False otherwise
        """
        pass

    def get_model_name(self) -> str:
        """
        Get the name of the model being used.

        Returns:
            Model name string
        """
        return "unknown"
