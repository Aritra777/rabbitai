"""ReAct agent implementation for RabbitAI"""

import json
import signal
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from rich.console import Console

from .tools.executor import CommandExecutor
from .context.system import SystemContext
from .logger import log_info, log_debug, log_warning, log_error


class TimeoutError(Exception):
    """Raised when LLM API call times out"""
    pass


def timeout_handler(_signum, _frame):
    raise TimeoutError("LLM API call timed out")


class ReactAgent:
    """Simple ReAct (Reasoning + Acting) agent for CLI troubleshooting"""

    def __init__(self, llm, config: Dict):
        """
        Initialize ReAct agent.

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
        log_info(f"ReactAgent initialized - max_iterations={self.max_iterations}, llm_timeout={self.llm_timeout}s")

        # ReAct prompt template
        self.react_prompt = ChatPromptTemplate.from_template("""
You are RabbitAI, a CLI troubleshooting assistant. Use the ReAct (Reasoning + Acting) pattern to solve the user's problem.

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

    def solve(self, user_query: str) -> str:
        """
        Main ReAct loop to solve the user's query.

        Args:
            user_query: The user's question or problem

        Returns:
            Final answer string
        """
        from rich.spinner import Spinner
        from rich.live import Live

        log_info(f"Starting ReAct solve loop for query: {user_query[:100]}")

        history = []
        os_info = self.system_context.get_os_info()
        shell_info = self.system_context.get_shell_info()
        available_commands = self.system_context.get_common_commands()

        # Main ReAct loop
        for iteration in range(self.max_iterations):
            log_debug(f"ReAct iteration {iteration + 1}/{self.max_iterations}")
            # Show separator between iterations (not for first iteration)
            if iteration > 0:
                self.console.print("\n[dim]" + "─" * 50 + "[/dim]\n")

            # Format history for prompt
            history_str = self._format_history(history)

            # Show loading animation while LLM is thinking
            spinner = Spinner("dots", text="[color(136)]Thinking...[/color(136)]", style="color(136)")

            # Get next action from LLM with timeout
            try:
                # Set alarm for timeout (Unix only)
                if hasattr(signal, 'SIGALRM'):
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(self.llm_timeout)

                try:
                    # Format the prompt
                    formatted_prompt = self.react_prompt.format(
                        user_query=user_query,
                        os_type=os_info["type"],
                        os_version=os_info["release"],
                        shell_type=shell_info["type"],
                        available_commands=", ".join(available_commands[:20]),
                        history=history_str
                    )

                    # Show spinner while getting LLM response
                    log_debug("Calling LLM API...")
                    with Live(spinner, console=self.console, transient=True):
                        result = self.llm.invoke(formatted_prompt)
                    log_debug(f"LLM response received (length: {len(result.content)} chars)")

                    # Cancel alarm
                    if hasattr(signal, 'SIGALRM'):
                        signal.alarm(0)

                except TimeoutError:
                    log_warning(f"LLM API timeout after {self.llm_timeout}s on iteration {iteration + 1}")
                    self.console.print(f"[yellow]⚠ LLM API timed out after {self.llm_timeout} seconds[/yellow]")
                    return f"The AI assistant timed out while processing your query. The issue might be too complex or the API is slow. Please try again or simplify your query."

                # Parse LLM decision
                decision = self._parse_decision(result.content)
                log_debug(f"LLM decision: action={decision['action']}, thought={decision.get('thought', '')[:50]}")

            except Exception as e:
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)  # Cancel alarm on error
                log_error(f"Error getting LLM response on iteration {iteration + 1}: {e}")
                self.console.print(f"[yellow]⚠ Error getting LLM response: {e}[/yellow]")
                return f"I encountered an error while processing your query: {str(e)}"

            # Don't show thoughts - removed
            # Don't show iteration count - removed

            # Add to history
            history.append({
                "iteration": iteration + 1,
                "thought": decision["thought"],
                "action": decision["action"]
            })

            # Execute action
            if decision["action"] == "final_answer":
                answer = decision.get("answer", "I don't have enough information to answer that.")
                log_info(f"ReAct completed with final_answer (length: {len(answer)} chars)")
                return answer

            elif decision["action"] == "execute_command":
                command = decision.get("command", "")
                if not command:
                    log_warning("execute_command action but no command provided")
                    continue

                log_info(f"Executing command: {command}")
                self.console.print(f"[color(94)]▶ Running:[/color(94)] [color(136)]{command}[/color(136)]")

                # Execute command
                result = self.executor.execute(command, os_info)
                log_debug(f"Command result: success={result['success']}, blocked={result['blocked']}")

                # Add observation to history
                history[-1]["command"] = command
                history[-1]["result"] = {
                    "success": result["success"],
                    "output": result["output"][:1000],
                    "error": result["error"][:500] if result["error"] else ""
                }

                # Display result
                if result["blocked"]:
                    self.console.print(f"[color(202)]✗ Blocked:[/color(202)] {result['error']}")
                elif result["success"]:
                    output_preview = result["output"][:200].strip()
                    if len(result["output"]) > 200:
                        output_preview += "..."
                    self.console.print(f"[color(244)]  Output:[/color(244)] {output_preview}")
                else:
                    self.console.print(f"[color(202)]✗ Error:[/color(202)] {result['error'][:200]}")

            else:
                log_warning(f"Unknown action type: {decision['action']}")
                self.console.print(f"[yellow]⚠ Unknown action: {decision['action']}[/yellow]")

        # Max iterations reached
        log_warning(f"Max iterations ({self.max_iterations}) reached without final answer")
        return self._generate_timeout_response(history, user_query)

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
