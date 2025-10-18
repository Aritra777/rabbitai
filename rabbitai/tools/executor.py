"""Command execution tool with safety checks for RabbitAI"""

import subprocess
import re
from typing import Dict, Any
from rich.console import Console
from ..logger import log_info, log_debug, log_warning
from ..command_config import DANGEROUS_PATTERNS, SAFE_COMMANDS, WRITE_INDICATORS


class CommandExecutor:
    """Executes shell commands with safety checks and user confirmation"""

    def __init__(self, config: Dict):
        """
        Initialize command executor.

        Args:
            config: Configuration dictionary with safety settings
        """
        self.config = config
        self.timeout = config.get('safety', {}).get('timeout_seconds', 30)
        self.require_confirmation = config.get('safety', {}).get('require_confirmation', True)
        self.console = Console()
        log_info(f"CommandExecutor initialized - timeout={self.timeout}s, require_confirmation={self.require_confirmation}")

        # Import safety patterns from config
        self.dangerous_patterns = DANGEROUS_PATTERNS
        self.safe_commands = SAFE_COMMANDS
        self.write_indicators = WRITE_INDICATORS

    def execute(self, command: str, os_info: Dict) -> Dict[str, Any]:
        """
        Execute a command with safety checks.

        Args:
            command: The command to execute
            os_info: Operating system information

        Returns:
            Dictionary with execution results:
            - success: bool - whether command succeeded
            - output: str - stdout from command
            - error: str - stderr from command
            - returncode: int - exit code
            - blocked: bool - whether command was blocked
        """
        # Validate command is not empty
        if not command or not command.strip():
            return {
                "success": False,
                "output": "",
                "error": "Empty command",
                "returncode": -1,
                "blocked": True
            }

        # Safety check for dangerous commands
        if self._is_dangerous(command):
            log_warning(f"Dangerous command blocked: {command}")
            self.console.print(f"[red]⚠ Dangerous command blocked:[/red] {command}")
            return {
                "success": False,
                "output": "",
                "error": "Command blocked: potentially dangerous operation",
                "returncode": -1,
                "blocked": True
            }

        # Ask for confirmation if needed
        if self.require_confirmation and not self._is_safe_command(command):
            log_debug(f"Requesting user confirmation for: {command}")
            if not self._get_user_confirmation(command):
                log_info("User declined command execution")
                return {
                    "success": False,
                    "output": "",
                    "error": "User declined to execute command",
                    "returncode": -1,
                    "blocked": True
                }
            log_info("User confirmed command execution")

        # Execute command
        return self._run_command(command)

    def _is_dangerous(self, command: str) -> bool:
        """
        Check if command matches dangerous patterns.

        Args:
            command: Command to check

        Returns:
            True if dangerous, False otherwise
        """
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False

    def _is_safe_command(self, command: str) -> bool:
        """
        Check if command is known to be safe (read-only).

        Args:
            command: Command to check

        Returns:
            True if safe, False otherwise
        """
        command_lower = command.strip().lower()

        for safe_cmd in self.safe_commands:
            if command_lower.startswith(safe_cmd.lower()):
                return True

        # Additional heuristic: if command has no write indicators
        return self._is_read_only_heuristic(command)

    def _is_read_only_heuristic(self, command: str) -> bool:
        """
        Simple heuristic to detect read-only commands.

        Args:
            command: Command to check

        Returns:
            True if appears read-only, False otherwise
        """
        command_lower = command.lower()
        return not any(indicator in command_lower for indicator in self.write_indicators)

    def _run_command(self, command: str) -> Dict[str, Any]:
        """
        Execute the command and capture output.

        Args:
            command: Command to execute

        Returns:
            Dictionary with execution results
        """
        try:
            log_debug(f"Executing command: {command}")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            log_debug(f"Command completed: returncode={result.returncode}, stdout_len={len(result.stdout)}, stderr_len={len(result.stderr)}")

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode,
                "blocked": False
            }

        except subprocess.TimeoutExpired:
            log_warning(f"Command timeout after {self.timeout}s: {command}")
            return {
                "success": False,
                "output": "",
                "error": f"Command timed out after {self.timeout} seconds",
                "returncode": -1,
                "blocked": False
            }
        except Exception as e:
            log_warning(f"Command execution error: {e} (command: {command})")
            return {
                "success": False,
                "output": "",
                "error": f"Execution error: {str(e)}",
                "returncode": -1,
                "blocked": False
            }

    def _get_user_confirmation(self, command: str) -> bool:
        """
        Ask user to confirm command execution.

        Args:
            command: Command to confirm

        Returns:
            True if user confirms, False otherwise
        """
        self.console.print(f"\n[color(136)]About to run:[/color(136)] [color(94)]{command}[/color(94)]")
        try:
            response = input("[color(136)]Continue? [y/N]:[/color(136)] ").strip().lower()
            return response in ['y', 'yes']
        except (EOFError, KeyboardInterrupt):
            self.console.print("\n[dim]Cancelled[/dim]")
            return False
