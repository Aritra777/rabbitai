"""Base agent class for RabbitAI ReAct agents"""

import json
import signal
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from rich.console import Console

from ..tools.executor import CommandExecutor
from ..context.system import SystemContext
from ..logger import log_info, log_debug, log_warning, log_error


class TimeoutError(Exception):
    """Raised when LLM API call times out"""
    pass


def timeout_handler(_signum, _frame):
    raise TimeoutError("LLM API call timed out")


class BaseAgent(ABC):
    """Base class for ReAct agents with common functionality"""

    def __init__(self, llm, config: Dict):
        """
        Initialize base agent.

        Args:
            llm: LLM instance (Gemini or Ollama)
            config: Configuration dictionary
        """
        self.llm = llm
        self.config = config
        self.executor = CommandExecutor(config)
        self.system_context = SystemContext()
        self.max_iterations = config.get('agent', {}).get('max_iterations', 10)
        self.llm_timeout = config.get('llm', {}).get('timeout_seconds', 30)
        self.console = Console()

        # ReAct prompt template (shared across all agents)
        self.react_prompt = ChatPromptTemplate.from_template("""
You are RabbitAI, a CLI assistant. You help users find files, diagnose issues, and perform system tasks by running shell commands.
Use the ReAct (Reasoning + Acting) pattern to solve the user's problem.

SYSTEM INFORMATION:
- OS: {os_type} {os_version}
- Shell: {shell_type}
- Available commands: {available_commands}

USER QUERY: {user_query}

PREVIOUS ACTIONS AND OBSERVATIONS:
{history}

INSTRUCTIONS:
Based on the user query and previous observations, decide your next action.

You can either:
1. Execute a command to gather more information
2. Provide a final answer if you have enough information

IMPORTANT:
- Use commands appropriate for {os_type}
- Start with simple diagnostic commands
- Build on previous observations
- Keep commands safe and read-only when possible
- Be concise and helpful

Respond in JSON format:
{{
    "thought": "your reasoning about what to do next and why",
    "action": "execute_command" or "final_answer",
    "command": "the command to run (only if action is execute_command)",
    "answer": "your final answer to the user (only if action is final_answer)"
}}

Make sure your response is valid JSON.""")

    @abstractmethod
    def solve(self, user_query: str) -> str:
        """
        Main method to solve the user's query.
        Must be implemented by subclasses.

        Args:
            user_query: The user's question or problem

        Returns:
            Final answer string
        """
        pass

    def _parse_decision(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured decision.

        Args:
            response: Raw LLM response

        Returns:
            Dictionary with decision fields

        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Handle markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            decision = json.loads(json_str)

            # Validate required fields
            if "action" not in decision:
                raise ValueError("Missing 'action' field")

            if decision["action"] == "execute_command" and "command" not in decision:
                raise ValueError("Missing 'command' field for execute_command action")

            if decision["action"] == "final_answer" and "answer" not in decision:
                raise ValueError("Missing 'answer' field for final_answer action")

            # Set defaults
            if "thought" not in decision:
                decision["thought"] = "Processing..."

            return decision

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}\nResponse: {response[:200]}")

    def _format_history(self, history: List[Dict]) -> str:
        """
        Format history for prompt.

        Args:
            history: List of previous actions

        Returns:
            Formatted history string
        """
        if not history:
            return "No previous actions yet. This is your first step."

        formatted = []
        for entry in history:
            formatted.append(f"\n--- Iteration {entry['iteration']} ---")
            formatted.append(f"Thought: {entry['thought']}")
            formatted.append(f"Action: {entry['action']}")

            if "command" in entry:
                formatted.append(f"Command: {entry['command']}")
                result = entry.get('result', {})
                formatted.append(f"Success: {result.get('success', False)}")

                if result.get('output'):
                    output = result['output'][:500]
                    formatted.append(f"Output: {output}")

                if result.get('error'):
                    formatted.append(f"Error: {result['error'][:200]}")

        return "\n".join(formatted)

    def _generate_timeout_response(self, history: List[Dict], user_query: str) -> str:
        """
        Generate response when max iterations reached.

        Args:
            history: List of previous actions
            user_query: Original user query

        Returns:
            Summary response
        """
        self.console.print(f"\n[yellow]⚠ Reached maximum iterations ({self.max_iterations})[/yellow]")

        # Try to get a summary from the LLM
        try:
            summary_prompt = f"""
Based on these diagnostic steps, provide a brief summary of what was discovered about this query:

Query: {user_query}

Steps taken:
{self._format_history(history)}

Provide a concise summary (2-3 sentences) of the findings."""

            response = self.llm.invoke(summary_prompt)
            return f"I've completed my diagnostic steps. Here's what I found:\n\n{response.content}"

        except Exception:
            # Fallback if LLM fails
            return (
                f"I've completed {len(history)} diagnostic steps but need more time to fully resolve this. "
                "Based on what I've found so far, you may want to run additional diagnostics manually."
            )
