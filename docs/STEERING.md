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

**Current Status:** v0.5 - Strands integration complete. Full tool-calling loop validated via AWS Bedrock. HailoRT upgrade to 5.2.0 needed to switch back to local inference.

### Session 2026-01-28
- Initialized project with UV
- Attempted Strands Agents SDK - encountered API incompatibilities with hailo-ollama
- Switched to httpx for direct API calls
- Implemented AgentNeo with streaming responses
- All core functionality working

### Session 2026-02-19
- Tested community Hailo Ollama Gateway as alternative to hailo-ollama (to enable tools/Strands support)
- Root cause of hailo-ollama limitation: returns HTTP 500 on any request with `tools` field
- Community gateway uses hailo_platform.genai Python API - needs system site-packages venv
- Initial model (Qwen2-1.5B-Instruct-Function-Calling-v1.hef) incompatible with HailoRT 5.1.1 (requires 5.2.0)
- Switched to Qwen2.5-1.5B-Instruct.hef - compatible with HailoRT 5.1.1
- **Tools field test PASSED** - gateway accepts tools without errors
- Gateway startup: requires `.venv_with_system` env in `/home/marcomark/Documents/code-projects/ollama_gateway`
- See `docs/GATEWAY_TEST_SESSION.md` for full details and startup instructions
- Next: Strands integration

### Session 2026-02-21 (Part 1)
- Completed full Strands integration (Phase 1)
- Removed LiteLLM; added strands-agents, httpx, ollama packages
- Created tools.py (get_current_time, get_weather via wttr.in)
- Created strands_agent.py with Strands Agent + tool registration
- Discovered Qwen2.5-1.5B-Instruct does not reliably invoke tools
- Switched to AWS Bedrock (Claude Haiku) — all 4 end-to-end tests passed
- Cut over main.py to Strands agent; deleted agent.py, provider.py, chat.py
- Outstanding: upgrade HailoRT to 5.2.0 to use function-calling HEF model for local inference
- Next: Phase 2 tools (MQTT, AWS Lambda, Amazon Polly)

### Session 2026-02-21 (Part 2) — HailoRT 5.1.1 → 5.2.0 upgrade
- Backed up all 5.1.1 packages to `~/Downloads/hailort-5.1.1-backup/`
- Installed `hailort 5.2.0` runtime and `hailort-pcie-driver 5.2.0`
- Package naming changed: `h10-hailort` → `hailort` (no h10 prefix in 5.2.0)
- Old PCIe driver removed first (naming conflict), then force-removed `h10-hailort`
- `python3-h10-hailort 5.1.1` retained (no 5.2.0 Python 3.13 package exists anywhere)
- Created compatibility symlinks so Python bindings still resolve:
  `/usr/lib/libhailort.so.5.1.1 → /usr/lib/libhailort.so.5.2.0`
- DKMS module built and installed for kernel 6.12.62+rpt-rpi-2712
- Reboot required to flash new SoC firmware (dmesg showed driver 5.2.0 vs pci_ep 5.1.1 mismatch)
- **NEXT SESSION: reboot first, then follow Steps 5–10 in STRANDS_INTEGRATION.md "Known Risk" section**

### Session 2026-02-21 (Part 3) — Python bindings ABI investigation
- Rebooted; HailoRT 5.2.0 hardware verified: CLI 5.2.0, firmware 5.2.0 (app), HAILO10H, `/dev/hailo0` present
- Community gateway started but ran in **mock mode** — `hailo_platform` Python bindings fail to import
- Root cause confirmed via `nm`: ABI break between `python3-h10-hailort 5.1.1` and `libhailort.so.5.2.0`
  - 5.1.1 Python bindings call: `Speech2TextGeneratorParams(Speech2TextTask, string_view)` — 2 params
  - 5.2.0 library exports: `Speech2TextGeneratorParams(Speech2TextTask, string_view, float)` — 3 params
  - The added `float` (likely `repetition_penalty`) changes the mangled symbol name — old `.so` can't find it
- `python3-hailort 4.23.0` (in apt) is the Hailo-8 product line — not compatible with H10H
- No 5.2.0 Python bindings for H10H/Python 3.13 found in apt or PyPI
- Options under investigation: build from source (Hailo GitHub), await Hailo release, roll back to 5.1.1, user has additional alternatives to try
- **NEXT SESSION: continue Python bindings investigation**

### Session 2026-02-21 (Part 4) — Rolled back to HailoRT 5.1.1
- hailo-ollama pull llama3.2:3b failed with null pointer error — root cause: hailo-ollama binary links against libhailort.so.5.1.1 which was symlinked to 5.2.0, causing runtime breakage even for network operations
- model server confirmed reachable at dev-public.hailo.ai:443 (from /etc/xdg/hailo-ollama/hailo-ollama.json)
- Rolled back to HailoRT 5.1.1: installed h10-hailort 5.1.1 + h10-hailort-pcie-driver 5.1.1 from backup debs
- Python bindings (hailo_platform) verified importing correctly with 5.1.1
- Reboot required to activate 5.1.1 driver/firmware
- **NEXT SESSION: reboot first, then follow steps in STRANDS_INTEGRATION.md "After 5.1.1 Rollback Reboot" section**

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

**Do not abandon the original approach and try something else without asking first.** There was a reason for the initial plan. Trust that judgement — if it hits a wall, stop and ask rather than pivoting to random alternatives.

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
**Tech Stack:** Python 3.13, UV, Strands Agents SDK, AWS Bedrock (Claude Haiku, temporary)
**Model (current):** `us.anthropic.claude-haiku-4-5-20251001-v1:0` via Bedrock — pending switch to local
**Model (target):** `Qwen2-1.5B-Instruct-Function-Calling-v1.hef` via community gateway
**HailoRT:** 5.1.1 (rolled back temporarily), awaiting reboot to activate 5.1.1 driver/firmware
**Run command:** `uv run agent-neo`

---

*This is a living document. Update as needed throughout development.*
