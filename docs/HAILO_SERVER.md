# Hailo-Ollama Server Guide

## Overview

hailo-ollama is an Ollama-compatible API server written in C++ on top of HailoRT. It runs on the Raspberry Pi AI HAT+ 2 (Hailo-10H NPU) and exposes a REST API for LLM inference.

## Quick Reference

| Setting | Value |
|---------|-------|
| Default Port | 8000 |
| API Base URL | `http://localhost:8000` |
| Model | `qwen2:1.5b` |

## Starting the Server

### Basic Command

```bash
hailo-ollama
```

The server starts with no required arguments and listens on `localhost:8000`.

### Verify Server is Running

```bash
curl http://localhost:8000/hailo/v1/list
```

This should return a list of available models.

## File Locations

| Path | Purpose |
|------|---------|
| `/usr/bin/hailo-ollama` | Executable (Debian package install) |
| `~/.local/bin/hailo-ollama` | Executable (source build) |
| `~/.config/hailo-ollama/hailo-ollama.json` | Configuration file |
| `~/.local/share/hailo-ollama/models/` | Model storage |

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/hailo/v1/list` | GET | List available models |
| `/api/pull` | POST | Download a model |
| `/api/chat` | POST | Chat with a model |

### Download a Model

```bash
curl --silent http://localhost:8000/api/pull \
  -H 'Content-Type: application/json' \
  -d '{"model": "qwen2:1.5b", "stream": true}'
```

### Test Chat

```bash
curl --silent http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"model": "qwen2:1.5b", "messages": [{"role": "user", "content": "Hello"}]}'
```

## AI Assistant Server Management

During development, Claude Code can start and monitor the hailo-ollama server using background task execution.

### Start Server (via Claude Code)

Claude Code will run:
```bash
hailo-ollama
```
in background mode and can monitor its output.

### Check Server Status

Claude Code can verify the server is responding:
```bash
curl -s http://localhost:8000/hailo/v1/list
```

### Stop Server

If needed, Claude Code can stop the background server process.

## Troubleshooting

### Server won't start
- Verify HailoRT is installed: `hailortcli fw-control identify`
- Check if another process is using port 8000: `lsof -i :8000`
- Ensure the Hailo-10H hardware is detected

### Connection refused
- Server may not be running - start it with `hailo-ollama`
- Check if the server is bound to the correct interface

### Model not found
- Download the model first using `/api/pull`
- Verify with `/hailo/v1/list`

---

## User Verification Needed

**Please verify these commands work on your system:**

1. [ ] `hailo-ollama` starts the server successfully
2. [ ] Server responds on `http://localhost:8000`
3. [ ] Model `qwen2:1.5b` is available via `/hailo/v1/list`

If any commands differ on your system, please let me know and I'll update this document.

---

## Sources

- [Hailo Model Zoo GenAI](https://github.com/hailo-ai/hailo_model_zoo_genai)
- [Raspberry Pi AI HAT+ 2 Announcement](https://www.raspberrypi.com/news/introducing-the-raspberry-pi-ai-hat-plus-2-generative-ai-on-raspberry-pi-5/)
- [Hailo Community Forum](https://community.hailo.ai/)
