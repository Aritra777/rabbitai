"""ReAct agent implementation for RabbitAI"""

import signal
from typing import Dict
from rich.spinner import Spinner
from rich.live import Live

from .baseagent import BaseAgent, TimeoutError, timeout_handler
from ..logger import log_info, log_debug, log_warning, log_error


class ReactAgent(BaseAgent):
    """Simple ReAct (Reasoning + Acting) agent for CLI troubleshooting"""

    def __init__(self, llm, config: Dict):
        """
        Initialize ReAct agent.

        Args:
            llm: LLM instance (Gemini or Ollama)
            config: Configuration dictionary
        """
        super().__init__(llm, config)
        log_info(f"ReactAgent initialized - max_iterations={self.max_iterations}, llm_timeout={self.llm_timeout}s")

    def solve(self, user_query: str) -> str:
        """
        Main ReAct loop to solve the user's query.

        Args:
            user_query: The user's question or problem

        Returns:
            Final answer string
        """
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
