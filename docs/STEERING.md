# Agent Neo - Steering & Interaction Guidelines

## Purpose

This document defines how we collaborate while building Agent Neo. It ensures consistent, efficient development across sessions and provides context for new AI conversations continuing this work.

## Interaction Protocol

### Before Making Changes

1. **Always ask permission** before creating or modifying code files
2. **Present plans** and wait for approval on significant decisions
3. **Explain reasoning** when recommending approaches

### During Development

1. **Work incrementally** - complete one task before moving to the next
2. **Test as we go** - verify each component works before proceeding
3. **Document decisions** - update REQUIREMENTS.md with important choices

### Communication Style

- Be concise and direct
- Use code examples when explaining concepts
- Highlight potential issues or risks upfront
- Ask clarifying questions rather than assuming

## Development Workflow

### Step-by-Step Process

```
1. Review current state
       ↓
2. Propose next action
       ↓
3. Wait for approval
       ↓
4. Implement change
       ↓
5. Verify/test
       ↓
6. Report results
       ↓
7. Return to step 1
```

### UV Commands Reference

| Action | Command |
|--------|---------|
| Initialize project | `uv init` |
| Add dependency | `uv add <package>` |
| Add dev dependency | `uv add --dev <package>` |
| Run script | `uv run python src/agent_neo/main.py` |
| Sync dependencies | `uv sync` |
| Show installed packages | `uv pip list` |

## Conventions

### Code Style

- Follow PEP 8
- Use type hints for function signatures
- Keep functions small and focused
- Prefer explicit over implicit

### Naming

- **Files:** lowercase with underscores (`model_provider.py`)
- **Classes:** PascalCase (`AgentNeo`)
- **Functions/variables:** snake_case (`send_message`)
- **Constants:** UPPER_SNAKE_CASE (`DEFAULT_MODEL`)

### File Organization

- One primary class/concept per file
- Keep imports organized: stdlib → third-party → local
- Configuration separate from logic

## Session Continuity

### Starting a New Session

When beginning a new AI conversation to continue this work:

1. **Read these documents first:**
   - `docs/REQUIREMENTS.md` - understand the project
   - `docs/STEERING.md` - understand how we work
   - `pyproject.toml` - see current dependencies

2. **Check current state:**
   - What files exist in `src/agent_neo/`?
   - What tasks are completed in REQUIREMENTS.md?
   - Are there any errors or issues to address?

3. **Resume from last checkpoint:**
   - Ask user where we left off if unclear
   - Review recent changes before proceeding

### Handoff Notes

Use this section to leave notes for future sessions:

```
[Session Date] - [Summary of progress]
- What was completed
- What's next
- Any blockers or issues
```

**Current Status:** v0.3 complete - Agent working with LiteLLM and streaming responses.

### Session 2026-01-28
- Initialized project with UV
- Attempted Strands Agents SDK - encountered API incompatibilities with hailo-ollama
- Switched to httpx for direct API calls
- Implemented AgentNeo with streaming responses
- All core functionality working

### Session 2026-01-29
- Replaced httpx with LiteLLM for unified LLM interface
- LiteLLMProvider replaces HailoOllamaClient
- Removed httpx dependency; litellm handles HTTP internally
- Model ID now uses LiteLLM format: `ollama/qwen2:1.5b`
- Supports future multi-provider expansion (Bedrock, etc.)

## Decision Log

Track significant decisions and their rationale here:

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-28 | Use UV exclusively | User requirement for modern Python tooling |
| 2026-01-28 | Python 3.13.5 | Current system version |
| 2026-01-28 | Tried Strands Agents SDK | Wanted agent/tool framework |
| 2026-01-28 | **Abandoned Strands SDK** | hailo-ollama returns 500 errors with `tools` field; unexplained errors through agent layer |
| 2026-01-28 | Switch to httpx directly | Simpler, reliable, full control over requests |
| 2026-01-28 | Implement streaming | Better UX - see responses as they generate |
| 2026-01-28 | No tool support | hailo-ollama doesn't support Ollama tools API |
| 2026-01-29 | Replace httpx with LiteLLM | Unified LLM interface, multi-provider support without custom client code |

## Escalation

If uncertain about a decision:

1. Present options with pros/cons
2. Make a recommendation
3. Wait for user decision
4. Document the choice

## When Stuck

**IMPORTANT:** If I encounter a blocker (cannot access a tool, command fails, missing dependency, etc.):

1. **Stop immediately** - do not attempt workarounds or alternative approaches
2. **Report the issue clearly** - explain what failed and why
3. **Ask for help** - wait for guidance before proceeding
4. **Resolve first** - do not move on until the blocking issue is addressed

This ensures we tackle problems head-on rather than accumulating technical debt or going down incorrect paths.

## Server Management

Claude Code can manage the hailo-ollama server during development and testing:

### Available Actions

| Action | How |
|--------|-----|
| Start server | Run `hailo-ollama` in background mode |
| Monitor output | Read from background task output |
| Check status | `curl http://localhost:8000/hailo/v1/list` |
| Stop server | Terminate background task |

### Workflow During Testing

1. Before testing, ask Claude Code to start the server
2. Claude Code runs `hailo-ollama` as a background task
3. Claude Code verifies server is responding
4. Run tests against the live server
5. When done, ask Claude Code to stop the server

See `docs/HAILO_SERVER.md` for full server documentation.

## Quick Reference

**Project:** Agent Neo
**Tech Stack:** Python 3.13, UV, LiteLLM, hailo-ollama
**API Base:** `http://localhost:8000`
**Model:** `ollama/qwen2:1.5b`
**Run command:** `uv run agent-neo`

---

*This is a living document. Update as needed throughout development.*
