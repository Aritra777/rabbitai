"""Configuration management for RabbitAI"""

import yaml
from pathlib import Path
from typing import Dict, Any
from .llm.ollama import OllamaLLM
from .llm.gemini import GeminiLLM


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
        from rich.prompt import Prompt, IntPrompt
        from rich.table import Table

        console = Console()
        config = self.default_config.copy()

        # Available Gemini models with descriptions
        GEMINI_MODELS = GeminiLLM.get_available_models()

        console.print("\n[bold color(136)]RabbitAI Setup[/bold color(136)]\n")

        # LLM Provider Selection
        console.print("[bold]Choose your LLM provider:[/bold]\n")
        console.print("  [color(136)]1.[/color(136)] Gemini - Google's Gemini (cloud, requires API key)")
        console.print("  [color(136)]2.[/color(136)] Ollama - Local models (free, requires Ollama installed)\n")

        provider_choice = IntPrompt.ask(
            "Select provider",
            choices=["1", "2"],
            default=1
        )
        provider = "gemini" if provider_choice == 1 else "ollama"
        config['llm']['provider'] = provider

        if provider == "gemini":
            console.print("\n[dim]Get your API key from: https://makersuite.google.com/app/apikey[/dim]")
            api_key = Prompt.ask("Enter Gemini API key", password=True)
            config['llm']['api_key'] = api_key

            # Gemini model selection with table
            console.print("\n[bold]Select a Gemini model:[/bold]\n")

            table = Table(show_header=False, box=None, padding=(0, 2))
            for idx, (model_id, description) in enumerate(GEMINI_MODELS, 1):
                table.add_row(
                    f"[color(136)]{idx}.[/color(136)]",
                    f"[bold]{model_id}[/bold]",
                    f"[dim]{description}[/dim]"
                )
            console.print(table)
            console.print()

            model_choice = IntPrompt.ask(
                "Select model",
                choices=[str(i) for i in range(1, len(GEMINI_MODELS) + 1)],
                default=1
            )
            config['llm']['model'] = GEMINI_MODELS[model_choice - 1][0]

        elif provider == "ollama":
            console.print("\n[dim]Fetching available Ollama models...[/dim]")
            ollama_models = OllamaLLM.get_available_models()

            if not ollama_models:
                console.print("[yellow]⚠ Could not fetch Ollama models. Make sure Ollama is installed and running.[/yellow]")
                console.print("[dim]Install models with: ollama pull <model>[/dim]")
                console.print("[dim]Popular models: llama3.2, llama3.1, mistral, codellama, phi3[/dim]\n")

                model = Prompt.ask("Enter Ollama model name", default="llama3.2")
                config['llm']['model'] = model
            else:
                console.print(f"\n[bold]Found {len(ollama_models)} installed model(s):[/bold]\n")

                table = Table(show_header=False, box=None, padding=(0, 2))
                for idx, model_name in enumerate(ollama_models, 1):
                    table.add_row(
                        f"[color(136)]{idx}.[/color(136)]",
                        f"[bold]{model_name}[/bold]"
                    )
                console.print(table)
                console.print()

                model_choice = IntPrompt.ask(
                    "Select model",
                    choices=[str(i) for i in range(1, len(ollama_models) + 1)],
                    default=1
                )
                config['llm']['model'] = ollama_models[model_choice - 1]

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