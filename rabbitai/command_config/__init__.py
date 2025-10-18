"""Configuration module for RabbitAI"""

from .safety_patterns import DANGEROUS_PATTERNS, SAFE_COMMANDS, WRITE_INDICATORS
from .os_commands import (
    COMMON_COMMANDS,
    LINUX_COMMANDS,
    MACOS_COMMANDS,
    WINDOWS_COMMANDS,
)

__all__ = [
    'DANGEROUS_PATTERNS',
    'SAFE_COMMANDS',
    'WRITE_INDICATORS',
    'COMMON_COMMANDS',
    'LINUX_COMMANDS',
    'MACOS_COMMANDS',
    'WINDOWS_COMMANDS',
]
