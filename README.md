# RabbitAI 🐰

An intelligent CLI troubleshooting assistant powered by LLMs using the ReAct (Reasoning + Acting) pattern.

RabbitAI helps you diagnose and troubleshoot system issues by autonomously running diagnostic commands, analyzing the results, and providing helpful answers - all through a simple conversational interface.

## Features

- **ReAct Pattern**: Uses iterative Reasoning + Acting to solve problems systematically
- **Multiple LLM Backends**: Support for Google Gemini (cloud) and Ollama (local)
- **Safety-First**: Built-in command safety checks, user confirmation, and dangerous command blocking
- **Smart Command Execution**: Automatically runs diagnostic commands based on your query
- **Clean UI**: Beautiful terminal interface with subtle brown color scheme and loading animations
- **Comprehensive Logging**: Detailed debug logs for troubleshooting and auditing
- **LangGraph Support**: Alternative LangGraph-based agent implementation available

## Installation

### Prerequisites

- **Python 3.8+** (Python 3.9 or later recommended)
- **pip** (Python package manager)
- **LLM Provider** (choose one):
  - **Gemini API**: Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
  - **Ollama**: Install from [ollama.ai](https://ollama.ai) and pull a model (e.g., `ollama pull llama3`)

### Install from GitHub

#### Option 1: Install with pip (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/rabbitai.git
cd rabbitai

# Install the package
pip install -e .
```

#### Option 2: Install from URL

```bash
# Install directly from GitHub
pip install git+https://github.com/yourusername/rabbitai.git
```

### Initial Setup

After installation, run the setup wizard:

```bash
rabbit setup
```

The setup wizard will ask you to:
1. Choose your LLM provider (Gemini or Ollama)
2. Enter your API key (for Gemini) or model name (for Ollama)
3. Configure safety settings

## Quick Start

### Basic Usage

```bash
# Start RabbitAI
rabbit

# Example interaction
rabbit> what directory am I in?
```

The agent will:
1. Analyze your query
2. Run diagnostic commands (e.g., `pwd`)
3. Provide a clear answer based on the output

### Example Queries

**System Diagnostics:**
```
rabbit> why is my disk full?
rabbit> what processes are using the most memory?
rabbit> check system uptime and load
```

**Network Troubleshooting:**
```
rabbit> can I reach google.com?
rabbit> what's my IP address?
rabbit> check if port 8080 is open
```

**Service Management:**
```
rabbit> is nginx running?
rabbit> what services are listening on port 80?
rabbit> check docker containers
```

**File Operations:**
```
rabbit> what are the largest files in this directory?
rabbit> find all .log files modified today
rabbit> show me hidden files
```

### Exit

```bash
rabbit> exit
# or press Ctrl+C
```

## Configuration

### Configuration File

RabbitAI stores its configuration at: `~/.rabbitai/config.yaml`

**Example configuration:**

```yaml
llm:
  provider: "gemini"           # or "ollama"
  model: "gemini-pro"          # or "llama3"
  api_key: "your-api-key"      # only for Gemini
  timeout_seconds: 30          # LLM API timeout

agent:
  max_iterations: 10           # Fixed at 10

safety:
  require_confirmation: true   # Always true
  timeout_seconds: 30          # Command execution timeout
```

### Reconfigure

To change your LLM provider or settings:

```bash
rabbit setup
```

## Logging

RabbitAI maintains detailed logs for debugging and auditing purposes.

### Log Location

Logs are stored in: `~/.rabbitai/logs/`

Log files are named by date: `rabbitai_YYYYMMDD.log`

### Log Levels

- **File logs**: All levels (DEBUG, INFO, WARNING, ERROR)
- **Console logs**: Only ERROR level (doesn't clutter your terminal)

### Log Rotation

- **Max file size**: 10 MB
- **Backup count**: 5 files
- **Total storage**: ~50 MB maximum

### What's Logged

The logs capture:
- Agent initialization and configuration
- User queries and responses
- LLM API calls and responses
- Command executions and results
- Safety checks and user confirmations
- Errors and timeouts
- Iteration progress

### Viewing Logs

```bash
# View today's log
tail -f ~/.rabbitai/logs/rabbitai_$(date +%Y%m%d).log

# Search for errors
grep ERROR ~/.rabbitai/logs/rabbitai_*.log

# View recent activity
tail -100 ~/.rabbitai/logs/rabbitai_$(date +%Y%m%d).log
```

## Architecture

### ReAct Pattern

RabbitAI uses the **ReAct (Reasoning + Acting)** pattern:

1. **Think**: Agent analyzes the query and decides on next action
2. **Act**: Execute a diagnostic command or provide final answer
3. **Observe**: Collect command output
4. **Repeat**: Continue until problem is solved (max 10 iterations)

### Components

```
rabbitai/
├── cli.py              # Main CLI interface and user interaction
├── config.py           # Configuration management
├── logger.py           # Logging infrastructure
├── agent.py            # Standard ReAct agent (loop-based)
├── reactagent.py       # LangGraph-based ReAct agent (alternative)
├── llm/
│   ├── base.py         # Base LLM interface
│   ├── gemini.py       # Google Gemini integration
│   └── ollama.py       # Ollama local LLM integration
├── tools/
│   └── executor.py     # Command execution with safety checks
└── context/
    └── system.py       # OS and shell detection
```

### Two Agent Implementations

RabbitAI includes two agent implementations:

1. **agent.py** (default): Simple loop-based ReAct agent
2. **reactagent.py**: LangGraph StateGraph-based agent

Both provide identical functionality and UI. To switch to the LangGraph version, edit `cli.py`:

```python
# Change from:
from .agent import ReactAgent

# To:
from .reactagent import ReactAgent
```

## Safety Features

### Command Safety Checks

RabbitAI includes multiple safety layers:

1. **Dangerous Command Blocking**: Automatically blocks destructive commands
   - `rm -rf`, `format`, `shutdown`, `mkfs`, etc.

2. **User Confirmation**: Always asks before running non-read-only commands
   - Write operations, installations, system modifications

3. **Safe Command Whitelist**: Auto-approves read-only commands
   - `ls`, `cat`, `grep`, `ps`, `df`, `ping`, etc.

4. **Timeout Protection**: Commands timeout after 30 seconds (configurable)

5. **LLM Timeout**: LLM API calls timeout after 30 seconds to prevent hanging

### Example Safety Flow

```bash
rabbit> install nginx

▶ Running: sudo apt-get install nginx

About to run: sudo apt-get install nginx
Continue? [y/N]: n

✗ Blocked: User declined to execute command
```

## Troubleshooting

### Common Issues

**1. "No configuration found"**
```bash
# Run setup first
rabbit setup
```

**2. "Gemini API key not configured"**
```bash
# Re-run setup and enter your API key
rabbit setup
```

**3. "Ollama connection error"**
```bash
# Make sure Ollama is running
ollama serve

# Pull a model if you haven't
ollama pull llama3
```

**4. "rabbit command not found"**

If the `rabbit` command isn't found after installation, you may need to add it to your PATH or create an alias:

**macOS/Linux (bash):**
```bash
# Add alias to bash profile
echo 'alias rabbit="python3 -m rabbitai.cli"' >> ~/.bashrc
source ~/.bashrc
```

**macOS (zsh - default on macOS Catalina and later):**
```bash
# Add alias to zsh profile
echo 'alias rabbit="python3 -m rabbitai.cli"' >> ~/.zshrc
source ~/.zshrc
```

**Linux (zsh):**
```bash
# Add alias to zsh profile
echo 'alias rabbit="python3 -m rabbitai.cli"' >> ~/.zshrc
source ~/.zshrc
```

**Windows (PowerShell):**
```powershell
# Add alias to PowerShell profile
Add-Content $PROFILE "`nSet-Alias -Name rabbit -Value 'python -m rabbitai.cli'"
# Reload profile
. $PROFILE
```

**Windows (Command Prompt):**
```batch
# Create a batch file in a directory that's in your PATH
# For example: C:\Windows\rabbit.bat
@echo off
python -m rabbitai.cli %*
```

**Alternative: Run directly without alias**
```bash
# Works on all platforms
python3 -m rabbitai.cli
# or on Windows
python -m rabbitai.cli
```

**5. "LLM API timed out"**
- The LLM is taking too long to respond
- Try simplifying your query
- Check your internet connection (for Gemini)
- Check Ollama is running (for local models)

### Debug Mode

For detailed troubleshooting, check the logs:

```bash
# Follow the log file in real-time
tail -f ~/.rabbitai/logs/rabbitai_$(date +%Y%m%d).log

# In another terminal, run RabbitAI
rabbit
```

The logs show:
- Exact prompts sent to the LLM
- LLM responses
- Command executions
- Error stack traces

## Dependencies

### Core Dependencies
- **langchain** - LLM orchestration framework
- **langgraph** - Graph-based agent workflows
- **langchain-google-genai** - Gemini integration
- **langchain-community** - Community LLM integrations
- **prompt_toolkit** - Interactive CLI with history
- **rich** - Beautiful terminal output
- **pydantic** - Data validation
- **pyyaml** - YAML configuration

### Dev Dependencies
- **pytest** - Testing framework
- **black** - Code formatter
- **flake8** - Linter
- **mypy** - Type checker

## License

MIT License - see LICENSE file for details

---

Made with ❤️ for CLI enthusiasts and system administrators
