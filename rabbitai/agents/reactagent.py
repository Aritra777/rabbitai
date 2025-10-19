"""LangGraph-based ReAct agent implementation for RabbitAI"""

import signal
from typing import List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from rich.spinner import Spinner
from rich.live import Live

from .baseagent import BaseAgent, TimeoutError, timeout_handler
from ..logger import log_info, log_debug, log_warning, log_error


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


class ReactAgent(BaseAgent):
    """LangGraph-based ReAct agent for CLI troubleshooting"""

    def __init__(self, llm, config: Dict):
        """
        Initialize LangGraph ReAct agent.

        Args:
            llm: LLM instance (Gemini or Ollama)
            config: Configuration dictionary
        """
        super().__init__(llm, config)

        # Build the graph
        self.graph = self._build_graph()
        log_info(f"LangGraphReactAgent initialized - max_iterations={self.max_iterations}, llm_timeout={self.llm_timeout}s")

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
                state["final_answer"] = self._generate_timeout_response_state(state)

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

    def _generate_timeout_response_state(self, state: AgentState) -> str:
        """
        Generate response when max iterations reached (state-based version).

        Args:
            state: AgentState containing history and user_query

        Returns:
            Summary response
        """
        return self._generate_timeout_response(state['history'], state['user_query'])
