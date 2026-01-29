# Agent Neo

A simple conversational AI agent using hailo-ollama on Raspberry Pi AI HAT+ 2.

## Requirements

- Raspberry Pi 5 with AI HAT+ 2 (Hailo-10H)
- hailo-ollama server installed and configured
- Python 3.13+
- UV package manager

## Setup

```bash
# Clone/enter the project directory
cd agent-neo

# Install dependencies (UV creates virtual environment automatically)
uv sync
```

## Usage

### 1. Start the hailo-ollama server

```bash
hailo-ollama
```

### 2. Run the agent

```bash
uv run agent-neo
```

Or run the module directly:

```bash
uv run python -m agent_neo.main
```

### 3. Chat

```
Agent Neo - Powered by hailo-ollama on Raspberry Pi AI HAT+ 2
Type 'quit' or 'exit' to end the conversation.
Type 'clear' to clear conversation history.

You: Hello! What can you do?
Agent Neo: Hello! I'm Agent Neo, a helpful AI assistant. I can answer questions,
have conversations, help with general knowledge, and more. How can I help you today?

You: quit
Goodbye!
```

## Configuration

Edit `src/agent_neo/config.py` to change settings:

```python
MODEL_ID = "ollama/qwen2:1.5b"         # LiteLLM model identifier
API_BASE = "http://localhost:8000"      # hailo-ollama server address
REQUEST_TIMEOUT = 120.0                 # Request timeout in seconds
```

## Available Models

Check available models on your hailo-ollama server:

```bash
curl http://localhost:8000/hailo/v1/list
```

Common models: `qwen2:1.5b`, `qwen2.5:1.5b`, `llama3.2:1b`, `deepseek_r1:1.5b`

## Project Structure

```
agent-neo/
├── docs/                   # Documentation
│   ├── REQUIREMENTS.md     # Design document
│   ├── STEERING.md         # Development guidelines
│   └── HAILO_SERVER.md     # Server management
├── src/agent_neo/          # Source code
│   ├── main.py             # Entry point
│   ├── agent.py            # AgentNeo class
│   ├── provider.py         # LiteLLMProvider
│   └── config.py           # Configuration
├── pyproject.toml          # Project config
└── README.md               # This file
```

## Architecture Note

This project uses **LiteLLM** as a unified LLM interface to communicate with hailo-ollama. LiteLLM provides a standard OpenAI-compatible API that can target multiple backends (Ollama, Bedrock, etc.) without custom client code. See `docs/REQUIREMENTS.md` for full details.

## Features

- Streaming responses (text appears as it's generated)
- Conversation history (multi-turn conversations)
- System prompt customization
- Unified LLM interface via LiteLLM (supports multiple providers)
