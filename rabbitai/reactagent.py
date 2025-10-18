"""LangGraph-based ReAct agent implementation for RabbitAI"""

import json
import signal
from typing import List, Dict, Any, TypedDict, Annotated
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live

from .tools.executor import CommandExecutor
from .context.system import SystemContext
from .logger import log_info, log_debug, log_warning, log_error


class TimeoutError(Exception):
    """Raised when LLM API call times out"""
    pass


def timeout_handler(_signum, _frame):
    raise TimeoutError("LLM API call timed out")


class AgentState(TypedDict):
    """State for the LangGraph agent"""
    user_query: str
    os_info: Dict[str, str]
    shell_info: Dict[str, str]
    available_commands: List[str]
    history: List[Dict[str, Any]]
    iteration: int
    max_iterations: int
    llm_timeout: int
    final_answer: str
    should_continue: bool


class ReactAgent:
    """LangGraph-based ReAct agent for CLI troubleshooting"""

    def __init__(self, llm, config: Dict):
        """
        Initialize LangGraph ReAct agent.

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

        # Build the graph
        self.graph = self._build_graph()
        log_info(f"LangGraphReactAgent initialized - max_iterations={self.max_iterations}, llm_timeout={self.llm_timeout}s")

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

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph"""

        # Create the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("execute_command", self._execute_command_node)

        # Set entry point
        workflow.set_entry_point("agent")

        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "execute": "execute_command",
                "end": END
            }
        )

        # Execute command goes back to agent
        workflow.add_edge("execute_command", "agent")

        return workflow.compile()

    def _agent_node(self, state: AgentState) -> AgentState:
        """Agent reasoning node - decides next action"""

        log_debug(f"LangGraph agent_node - iteration {state['iteration'] + 1}/{state['max_iterations']}")

        # Show separator between iterations (not for first iteration)
        if state["iteration"] > 0:
            self.console.print("\n[dim]" + "─" * 50 + "[/dim]\n")

        # Format history for prompt
        history_str = self._format_history(state["history"])

        # Show loading animation
        spinner = Spinner("dots", text="[color(136)]Thinking...[/color(136)]", style="color(136)")

        # Get next action from LLM with timeout
        try:
            # Set alarm for timeout (Unix only)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(state["llm_timeout"])

            try:
                # Format the prompt
                formatted_prompt = self.react_prompt.format(
                    user_query=state["user_query"],
                    os_type=state["os_info"]["type"],
                    os_version=state["os_info"]["release"],
                    shell_type=state["shell_info"]["type"],
                    available_commands=", ".join(state["available_commands"][:20]),
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
                log_warning(f"LLM API timeout after {state['llm_timeout']}s on iteration {state['iteration'] + 1}")
                self.console.print(f"[yellow]⚠ LLM API timed out after {state['llm_timeout']} seconds[/yellow]")
                state["final_answer"] = "The AI assistant timed out while processing your query. The issue might be too complex or the API is slow. Please try again or simplify your query."
                state["should_continue"] = False
                return state

            # Parse LLM decision
            decision = self._parse_decision(result.content)
            log_debug(f"LLM decision: action={decision['action']}, thought={decision.get('thought', '')[:50]}")

        except Exception as e:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
            log_error(f"Error getting LLM response on iteration {state['iteration'] + 1}: {e}")
            self.console.print(f"[yellow]⚠ Error getting LLM response: {e}[/yellow]")
            state["final_answer"] = f"I encountered an error while processing your query: {str(e)}"
            state["should_continue"] = False
            return state

        # Update state with decision
        state["iteration"] += 1

        # Add to history
        history_entry = {
            "iteration": state["iteration"],
            "thought": decision["thought"],
            "action": decision["action"]
        }

        if decision["action"] == "final_answer":
            answer = decision.get("answer", "I don't have enough information to answer that.")
            log_info(f"LangGraph completed with final_answer (length: {len(answer)} chars)")
            state["final_answer"] = answer
            state["should_continue"] = False
        elif decision["action"] == "execute_command":
            command = decision.get("command", "")
            if command:
                log_info(f"Executing command: {command}")
                history_entry["command"] = command
                state["history"].append(history_entry)
                state["should_continue"] = True
            else:
                log_warning("execute_command action but no command provided")
                # No command provided, continue
                state["should_continue"] = True
        else:
            log_warning(f"Unknown action type: {decision['action']}")
            self.console.print(f"[yellow]⚠ Unknown action: {decision['action']}[/yellow]")
            state["should_continue"] = True

        # Check max iterations
        if state["iteration"] >= state["max_iterations"]:
            log_warning(f"Max iterations ({state['max_iterations']}) reached without final answer")
            state["should_continue"] = False
            if not state["final_answer"]:
                state["final_answer"] = self._generate_timeout_response(state)

        return state

    def _execute_command_node(self, state: AgentState) -> AgentState:
        """Execute command node"""

        log_debug("LangGraph execute_command_node")

        # Get the last history entry with the command
        if not state["history"]:
            return state

        last_entry = state["history"][-1]
        command = last_entry.get("command", "")

        if not command:
            return state

        self.console.print(f"[color(94)]▶ Running:[/color(94)] [color(136)]{command}[/color(136)]")

        # Execute command
        result = self.executor.execute(command, state["os_info"])
        log_debug(f"Command result: success={result['success']}, blocked={result['blocked']}")

        # Add observation to history
        last_entry["result"] = {
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

        return state

    def _should_continue(self, state: AgentState) -> str:
        """Determine if we should continue or end"""
        if state["should_continue"] and state["iteration"] < state["max_iterations"]:
            return "execute"
        else:
            return "end"

    def solve(self, user_query: str) -> str:
        """
        Main entry point to solve the user's query using LangGraph.

        Args:
            user_query: The user's question or problem

        Returns:
            Final answer string
        """
        log_info(f"Starting LangGraph solve for query: {user_query[:100]}")

        # Initialize state
        initial_state: AgentState = {
            "user_query": user_query,
            "os_info": self.system_context.get_os_info(),
            "shell_info": self.system_context.get_shell_info(),
            "available_commands": self.system_context.get_common_commands(),
            "history": [],
            "iteration": 0,
            "max_iterations": self.max_iterations,
            "llm_timeout": self.llm_timeout,
            "final_answer": "",
            "should_continue": True
        }

        # Run the graph
        final_state = self.graph.invoke(initial_state)

        return final_state["final_answer"]

    def _parse_decision(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured decision"""
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
        """Format history for prompt"""
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

    def _generate_timeout_response(self, state: AgentState) -> str:
        """Generate response when max iterations reached"""
        self.console.print(f"\n[yellow]⚠ Reached maximum iterations ({state['max_iterations']})[/yellow]")

        # Try to get a summary from the LLM
        try:
            summary_prompt = f"""
Based on these diagnostic steps, provide a brief summary of what was discovered about this query:

Query: {state['user_query']}

Steps taken:
{self._format_history(state['history'])}

Provide a concise summary (2-3 sentences) of the findings."""

            response = self.llm.invoke(summary_prompt)
            return f"I've completed my diagnostic steps. Here's what I found:\n\n{response.content}"

        except Exception:
            # Fallback if LLM fails
            return (
                f"I've completed {len(state['history'])} diagnostic steps but need more time to fully resolve this. "
                "Based on what I've found so far, you may want to run additional diagnostics manually."
            )
