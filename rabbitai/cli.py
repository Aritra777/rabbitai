"""Main CLI interface for RabbitAI"""

import sys
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from .config import Config
from .agent import ReactAgent
from .context.system import SystemContext
from .llm.gemini import GeminiLLM
from .llm.ollama import OllamaLLM
from .logger import get_logger, log_info, log_error, log_exception


def main():
    """Main entry point for RabbitAI CLI"""
    console = Console()
    logger = get_logger()

    log_info("RabbitAI CLI started")

    # Parse command line arguments
    args = sys.argv[1:]

    # Handle 'setup' command
    if len(args) > 0 and args[0] == 'setup':
        log_info("Running setup command")
        config_manager = Config()
        config_manager.setup_interactive()
        log_info("Setup completed")
        return

    # Load configuration
    config_manager = Config()
    config = config_manager.load()
    log_info(f"Configuration loaded from {config_manager.get_config_path()}")

    # Check if setup is needed
    if not config_manager.config_exists():
        log_error("No configuration found")
        console.print("[yellow]⚠ No configuration found.[/yellow]\n")
        console.print("Please run: [cyan]rabbit setup[/cyan]\n")
        return

    # Initialize LLM
    try:
        llm_config = config['llm']
        log_info(f"Initializing LLM: provider={llm_config['provider']}, model={llm_config.get('model', 'unknown')}")

        if llm_config['provider'] == 'gemini':
            if not llm_config.get('api_key'):
                log_error("Gemini API key not configured")
                console.print("[red]❌ Gemini API key not configured.[/red]")
                console.print("Run: [cyan]rabbit setup[/cyan]\n")
                return
            llm = GeminiLLM(llm_config['api_key'], llm_config.get('model', 'gemini-pro'))
            log_info("Gemini LLM initialized successfully")
        else:
            llm = OllamaLLM(llm_config.get('model', 'llama3'))
            log_info("Ollama LLM initialized successfully")

        # Quick availability check (non-blocking)
        console.print("[dim]Initializing AI...[/dim]")

    except Exception as e:
        log_exception(f"Failed to initialize LLM: {e}")
        console.print(f"[red]❌ Failed to initialize LLM: {e}[/red]")
        console.print("Check your configuration and try again.\n")
        return

    # Initialize agent and system context
    agent = ReactAgent(llm, config)
    system_context = SystemContext()
    log_info(f"Agent initialized - OS: {system_context.get_os_info()['type']}, Shell: {system_context.get_shell_info()['type']}")

    # Welcome message with brown theme
    console.print(Panel(
        f"[bold color(136)]Welcome to RabbitAI[/bold color(136)]\n"
        f"[color(94)]Your AI CLI Assistant[/color(94)]\n\n"
        f"[dim]Using:[/dim] {llm_config['provider'].title()} ({llm.get_model_name()})\n"
        f"[dim]OS:[/dim] {system_context.get_os_info()['type'].title()}\n"
        f"[dim]Shell:[/dim] {system_context.get_shell_info()['type']}",
        title="[color(136)]🐰 RabbitAI[/color(136)]",
        border_style="color(94)"
    ))

    console.print("\n[color(244)]Type your question or problem. Type 'exit' to quit.[/color(244)]\n")

    # Interactive loop
    history = InMemoryHistory()
    log_info("Starting interactive loop")

    while True:
        try:
            user_input = prompt('rabbit> ', history=history)

            if user_input.lower() in ['exit', 'quit', 'bye']:
                log_info("User requested exit")
                console.print("[dim]Goodbye![/dim]")
                break

            if user_input.strip() == '':
                continue

            # Process query through agent
            log_info(f"Processing user query: {user_input[:100]}")
            console.print()
            response = agent.solve(user_input)
            log_info(f"Agent response generated (length: {len(response)} chars)")

            # Display response with brown theme
            console.print(f"\n[bold color(136)]Answer:[/bold color(136)]")
            console.print(Markdown(response))
            console.print()

        except (EOFError, KeyboardInterrupt):
            log_info("User interrupted (EOF/Ctrl+C)")
            console.print("\n[dim]Goodbye![/dim]")
            break
        except Exception as e:
            log_exception(f"Error in interactive loop: {e}")
            console.print(f"\n[red]❌ Error: {e}[/red]\n")
            import traceback
            if '--debug' in sys.argv:
                traceback.print_exc()


if __name__ == "__main__":
    main()
