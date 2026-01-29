# Agent Neo - Requirements & Design Document

## Project Overview

**Project Name:** Agent Neo
**Type:** Python-based AI Agent
**Purpose:** Test and interact with a local LLM hosted on Raspberry Pi with AI HAT+ 2

## Goals

1. Create a simple, functional conversational agent
2. Connect to a local LLM served via hailo-ollama
3. Demonstrate basic chat capabilities with streaming responses
4. Serve as a foundation for future agent development

## Technical Requirements

### Environment

| Requirement | Specification |
|-------------|---------------|
| Platform | Raspberry Pi 5 with AI HAT+ 2 |
| Python | 3.13.5 |
| Package Manager | UV (exclusive) |
| Virtual Environment | Managed by UV |

### Dependencies

| Package | Purpose |
|---------|---------|
| `litellm` | Unified LLM interface for communicating with hailo-ollama (and other providers) |

### Local LLM Configuration

| Setting | Value |
|---------|-------|
| Server | hailo-ollama |
| API Base | `http://localhost:8000` |
| Model | `ollama/qwen2:1.5b` (LiteLLM format) |
| Protocol | Ollama-compatible API via LiteLLM |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Agent Neo                          │
│  ┌─────────────────┐    ┌─────────────────────────┐    │
│  │   AgentNeo      │───▶│  LiteLLMProvider        │    │
│  │   (Chat Loop)   │    │   (litellm)             │    │
│  └─────────────────┘    └───────────┬─────────────┘    │
│                                     │                   │
└─────────────────────────────────────┼───────────────────┘
                                      │ litellm.completion()
                                      ▼
                         ┌─────────────────────────┐
                         │    hailo-ollama         │
                         │  localhost:8000         │
                         │  Model: qwen2:1.5b      │
                         └─────────────────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │    AI HAT+ 2 (NPU)      │
                         │   Hailo-10H Accelerator │
                         └─────────────────────────┘
```

## Project Structure

```
agent-neo/
├── docs/
│   ├── REQUIREMENTS.md      # This document
│   ├── STEERING.md          # Interaction guidelines
│   └── HAILO_SERVER.md      # Server startup and management
├── src/
│   └── agent_neo/
│       ├── __init__.py      # Package init
│       ├── main.py          # Entry point, CLI
│       ├── agent.py         # AgentNeo class with chat loop
│       ├── provider.py      # LiteLLMProvider
│       └── config.py        # Configuration constants
├── pyproject.toml           # UV/project configuration
├── .python-version          # Python version pin
└── README.md                # Usage instructions
```

## Implementation Tasks

### Phase 1: Project Setup - COMPLETE
- [x] Initialize UV project with `uv init`
- [x] Configure pyproject.toml with dependencies
- [x] Set Python version
- [x] Create directory structure

### Phase 2: Core Implementation - COMPLETE
- [x] Create config.py with LLM settings
- [x] Implement LLM provider (migrated from httpx to LiteLLM)
- [x] Create AgentNeo class with conversation management
- [x] Create main.py entry point with interactive loop
- [x] Implement streaming responses

### Phase 3: Testing & Validation - COMPLETE
- [x] Test connection to hailo-ollama endpoint
- [x] Verify agent can send/receive messages
- [x] Test basic conversation flow
- [x] Test streaming responses

### Phase 4: Documentation - COMPLETE
- [x] Update README with usage instructions
- [x] Document configuration options
- [x] Document architecture changes (Strands → httpx → LiteLLM)

## API Reference

### hailo-ollama Chat Endpoint

**Endpoint:** `POST http://localhost:8000/api/chat`

**Request Format:**
```json
{
  "model": "qwen2:1.5b",
  "messages": [
    {"role": "system", "content": "System prompt here"},
    {"role": "user", "content": "Hello"}
  ],
  "stream": true
}
```

**Response Format (streaming):**
```json
{"model":"qwen2:1.5b","message":{"role":"assistant","content":"Hello"},"done":false}
{"model":"qwen2:1.5b","message":{"role":"assistant","content":"!"},"done":false}
{"model":"qwen2:1.5b","message":{"role":"assistant","content":""},"done":true}
```

### API Limitations

hailo-ollama implements a **subset** of the Ollama API:

| Feature | Supported |
|---------|-----------|
| Basic chat | Yes |
| Streaming | Yes |
| System prompts | Yes |
| Conversation history | Yes |
| Tools/Functions | **No** |
| Options field | Yes |

## Architecture Decision: Strands SDK to httpx

### What We Tried

Initially, we attempted to use the **Strands Agents SDK** with its built-in Ollama provider. This would have provided:
- Agent/tool framework
- Conversation management
- Structured tool calling

### Why It Didn't Work

Testing revealed **API incompatibilities** between Strands' Ollama provider and hailo-ollama:

1. **Tools field causes errors** - hailo-ollama returns HTTP 500 if the request contains a `tools` field, even an empty array `[]`

2. **Additional request fields** - Even after creating a custom provider to remove the `tools` field, unexplained 500 errors persisted when requests were made through the Strands Agent

3. **Direct API works** - Direct `curl` requests to hailo-ollama worked perfectly, confirming the issue was in the SDK layer

### Decision

We switched to using **httpx directly** for the following reasons:

1. **Simpler** - Direct HTTP calls with full control over request format
2. **Reliable** - No middleware causing mysterious errors
3. **Sufficient** - hailo-ollama doesn't support tools anyway, so Strands' main value proposition wasn't applicable
4. **Fewer dependencies** - Removed strands-agents, boto3, ollama; kept only httpx

### Trade-offs

| Lost | Gained |
|------|--------|
| Strands agent framework | Simpler, more reliable code |
| Tool calling abstraction | (N/A - hailo-ollama doesn't support tools) |
| Conversation management | Custom implementation (simple) |

## Resolved Questions

1. ~~Does hailo-ollama use standard Ollama API format?~~ **Partial - basic chat works, but tools don't**
2. ~~What Python version?~~ **Python 3.13.5**
3. ~~Streaming responses?~~ **Yes, implemented with LiteLLM streaming**
4. ~~Tool support?~~ **Not possible - hailo-ollama doesn't support the tools API**

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-28 | 0.1 | Initial draft |
| 2026-01-28 | 0.2 | Switched from Strands SDK to httpx due to API incompatibilities |
| 2026-01-29 | 0.3 | Replaced httpx with LiteLLM for unified LLM interface |
