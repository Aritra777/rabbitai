"""System context detection for RabbitAI"""

import platform
import os
import subprocess
from typing import Dict, List


class SystemContext:
    """Detects and provides system information"""

    def __init__(self):
        self._os_info = None
        self._shell_info = None
        self._common_commands = None

    def get_os_info(self) -> Dict[str, str]:
        """
        Get operating system information.

        Returns:
            Dictionary with OS details (type, version, machine)
        """
        if self._os_info is None:
            system = platform.system().lower()

            # Normalize OS names
            if system == "darwin":
                os_type = "macos"
            else:
                os_type = system

            self._os_info = {
                'type': os_type,
                'system': system,  # Original value for internal use
                'version': platform.version(),
                'release': platform.release(),
                'machine': platform.machine(),
                'processor': platform.processor() or 'unknown'
            }
        return self._os_info

    def get_shell_info(self) -> Dict[str, str]:
        """
        Get shell information.

        Returns:
            Dictionary with shell details (type, path)
        """
        if self._shell_info is None:
            shell = os.environ.get('SHELL', '/bin/sh')
            shell_name = os.path.basename(shell)

            self._shell_info = {
                'type': shell_name,
                'path': shell,
                'term': os.environ.get('TERM', 'unknown')
            }
        return self._shell_info

    def get_common_commands(self) -> List[str]:
        """
        Get list of common commands available on the system.

        Returns:
            List of command names
        """
        if self._common_commands is not None:
            return self._common_commands

        os_info = self.get_os_info()
        os_type = os_info['system']  # Use original value

        # Base commands available on most systems
        common = ['echo', 'cat', 'ls', 'pwd', 'whoami', 'date']

        # OS-specific commands
        if os_type in ['linux', 'darwin']:
            common.extend([
                'ping', 'ps', 'grep', 'find', 'which', 'whereis',
                'df', 'du', 'top', 'netstat', 'curl', 'wget'
            ])

            if os_type == 'linux':
                common.extend([
                    'systemctl', 'journalctl', 'ip', 'ss', 'free',
                    'lsof', 'uname', 'hostname', 'uptime'
                ])
            elif os_type == 'darwin':  # macOS
                common.extend([
                    'launchctl', 'route', 'lsof', 'ifconfig',
                    'uname', 'hostname', 'uptime'
                ])

        elif os_type == 'windows':
            common = [
                'ping', 'ipconfig', 'tasklist', 'netstat', 'sc',
                'wmic', 'dir', 'type', 'echo', 'where', 'hostname'
            ]

        # Filter to only commands that are actually available
        self._common_commands = self._filter_available_commands(common)
        return self._common_commands

    def _filter_available_commands(self, commands: List[str]) -> List[str]:
        """
        Filter command list to only those available on the system.

        Args:
            commands: List of command names to check

        Returns:
            List of available commands
        """
        available = []
        os_info = self.get_os_info()

        for cmd in commands:
            if self._command_exists(cmd, os_info['system']):
                available.append(cmd)

        return available

    def _command_exists(self, command: str, os_type: str) -> bool:
        """
        Check if a command exists on the system.

        Args:
            command: Command name to check
            os_type: Operating system type

        Returns:
            True if command exists, False otherwise
        """
        try:
            if os_type == 'windows':
                # On Windows, use 'where' command
                result = subprocess.run(
                    ['where', command],
                    capture_output=True,
                    check=False,
                    timeout=2
                )
            else:
                # On Unix-like systems, use 'which' command
                result = subprocess.run(
                    ['which', command],
                    capture_output=True,
                    check=False,
                    timeout=2
                )

            return result.returncode == 0

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False

    def get_summary(self) -> str:
        """
        Get a human-readable summary of system information.

        Returns:
            Formatted string with system details
        """
        os_info = self.get_os_info()
        shell_info = self.get_shell_info()

        return (
            f"OS: {os_info['type'].title()} {os_info['release']}\n"
            f"Machine: {os_info['machine']}\n"
            f"Shell: {shell_info['type']}\n"
            f"Available commands: {len(self.get_common_commands())}"
        )
