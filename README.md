# RabbitAI 🐰

An intelligent CLI troubleshooting assistant powered by LLMs using the ReAct (Reasoning + Acting) pattern.

RabbitAI helps you diagnose and troubleshoot system issues by autonomously running diagnostic commands, analyzing the results, and providing helpful answers - all through a simple conversational interface.

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

After installation, the `rabbit` command may not be in your PATH. Add the scripts directory to your PATH:

**macOS:**
```bash
# Add to ~/.zshrc or ~/.bash_profile
export PATH="$HOME/Library/Python/3.9/bin:$PATH" # Replace the python version as per your current version
source ~/.zshrc
```

**Linux:**
```bash
# Add to ~/.bashrc or ~/.profile
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc
```

**Windows:**
```powershell
# Add to PowerShell profile or Environment Variables
$env:PATH += ";$env:APPDATA\Python\Python39\Scripts" # Replace the python version as per your current version
```

**Alternative: Run directly without PATH setup**
```bash
python3 -m rabbitai.cli  # macOS/Linux
python -m rabbitai.cli   # Windows
```

## License

MIT License - see LICENSE file for details

---

Made with ❤️ for CLI enthusiasts and system administrators
