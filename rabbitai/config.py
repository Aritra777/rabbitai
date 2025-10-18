"""Configuration management for RabbitAI"""

import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """Manages RabbitAI configuration"""

    def __init__(self):
        self.config_dir = Path.home() / ".rabbitai"
        self.config_file = self.config_dir / "config.yaml"
        self.default_config = {
            'llm': {
                'provider': 'gemini',
                'model': 'gemini-pro',
                'api_key': None,
                'timeout_seconds': 30,  # LLM API timeout
            },
            'agent': {
                'max_iterations': 10,  # Fixed, not configurable
            },
            'safety': {
                'require_confirmation': True,  # Always true
                'timeout_seconds': 30,  # Command execution timeout
            }
        }

    def load(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults"""
        if not self.config_file.exists():
            return self.default_config.copy()

        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                # Merge with defaults to ensure all keys exist
                return self._merge_with_defaults(config)
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
            return self.default_config.copy()

    def save(self, config: Dict[str, Any]):
        """Save configuration to file"""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded config with defaults to ensure all keys exist"""
        merged = self.default_config.copy()
        for key, value in config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key].update(value)
            else:
                merged[key] = value
        return merged

    def setup_interactive(self):
        """Interactive configuration setup"""
        from rich.console import Console
        from rich.prompt import Prompt

        console = Console()
        config = self.default_config.copy()

        console.print("\n[bold color(136)]RabbitAI Setup[/bold color(136)]\n")

        # LLM Provider
        console.print("[dim]Choose your LLM provider:[/dim]")
        console.print("  [color(136)]gemini[/color(136)] - Google's Gemini (cloud, requires API key)")
        console.print("  [color(136)]ollama[/color(136)] - Local models (free, requires Ollama installed)\n")

        provider = Prompt.ask(
            "LLM provider",
            choices=["gemini", "ollama"],
            default="gemini"
        )
        config['llm']['provider'] = provider

        if provider == "gemini":
            console.print("\n[dim]Get your API key from: https://makersuite.google.com/app/apikey[/dim]")
            api_key = Prompt.ask("Enter Gemini API key", password=True)
            config['llm']['api_key'] = api_key

            model = Prompt.ask(
                "Model name",
                default="gemini-pro"
            )
            config['llm']['model'] = model

        elif provider == "ollama":
            console.print("\n[dim]Make sure Ollama is running: ollama serve[/dim]")
            console.print("[dim]Popular models: llama3, codellama, mistral[/dim]")

            model = Prompt.ask("Enter Ollama model name", default="llama3")
            config['llm']['model'] = model

        # Timeouts (optional configuration)
        console.print("\n[bold]Timeout Settings[/bold]")
        console.print("[dim]Set timeouts for LLM API calls and command execution[/dim]")

        llm_timeout = int(Prompt.ask(
            "LLM API timeout (seconds)",
            default="30"
        ))
        config['llm']['timeout_seconds'] = llm_timeout

        cmd_timeout = int(Prompt.ask(
            "Command execution timeout (seconds)",
            default="30"
        ))
        config['safety']['timeout_seconds'] = cmd_timeout

        # Note: max_iterations and require_confirmation are fixed
        config['agent']['max_iterations'] = 10
        config['safety']['require_confirmation'] = True

        # Save configuration
        self.save(config)
        console.print("\n[color(34)]✓ Configuration saved to:[/color(34)] [color(136)]{}[/color(136)]".format(self.config_file))
        console.print("\n[dim]Note: Max iterations fixed at 10, command confirmation always required[/dim]")
        console.print("[dim]You can edit the config file directly or run 'rabbit setup' again to reconfigure.[/dim]\n")

    def config_exists(self) -> bool:
        """Check if configuration file exists"""
        return self.config_file.exists()

    def get_config_path(self) -> Path:
        """Get path to configuration file"""
        return self.config_file
