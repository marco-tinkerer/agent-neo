# Agent Neo — Strands Integration Plan

**Created:** 2026-02-20
**Status:** ✅ COMPLETE — Phase 1 fully implemented and validated
**Owner:** Active development session

---

## Purpose of This Document

This is the primary planning and status tracking document for the Strands Agents SDK integration into Agent Neo. It contains enough context for a new conversation to understand the project, the decisions made, and pick up implementation at the current task without any additional input.

Read this document alongside:
- `docs/REQUIREMENTS.md` — overall project design decisions
- `docs/STEERING.md` — interaction protocol, session history, conventions
- `docs/GATEWAY_TEST_SESSION.md` — community gateway test results (prerequisite for this work)

---

## Background

Agent Neo is a conversational AI agent running on a **Raspberry Pi 5 with Hailo-10H NPU (AI HAT+ 2)**. The current stable implementation (v0.4) uses **LiteLLM** to talk to `hailo-ollama` (port 8000) for basic streaming chat — no tool calling.

The goal of this integration is to add **tool calling capability** via the **Strands Agents SDK**, which enables the agent to take real-world actions (query APIs, send messages, invoke cloud services, etc.) as part of a conversation.

### Why Not Use Strands from the Start?

Strands was the original target framework but was blocked: `hailo-ollama` returns HTTP 500 on any request containing a `tools` field. A community-built alternative gateway was found, validated, and is now the foundation for this integration.

### Why the Community Gateway?

The **Hailo Ollama Gateway** (`/home/marcomark/Documents/code-projects/ollama_gateway`) is a FastAPI server exposing an Ollama-compatible REST API backed by `hailo_platform.genai`. Unlike `hailo-ollama`, it accepts the `tools` field required by Strands.

**Gateway validation results (2026-02-19):**
- ✅ Model listing endpoint works
- ✅ Streaming responses work (318 chunks received)
- ✅ Tools field accepted — HTTP 200, no errors
- ❌ Non-streaming chat times out (irrelevant — Strands uses streaming)

See `test_results_qwen25_120s.log` for the raw test output.

---

## Current Project State

### File Structure
```
agent-neo/
├── src/agent_neo/
│   ├── config.py          # MODEL_ID, API_BASE (port 8000), REQUEST_TIMEOUT
│   ├── provider.py        # LiteLLMProvider — wraps litellm.completion()
│   ├── agent.py           # AgentNeo — manages conversation history, calls provider
│   └── main.py            # Interactive CLI loop (entry point: `uv run agent-neo`)
├── docs/
│   ├── REQUIREMENTS.md
│   ├── STEERING.md
│   ├── HAILO_SERVER.md
│   ├── GATEWAY_TEST_SESSION.md
│   └── STRANDS_INTEGRATION.md  ← this file
├── test_gateway.py             # Gateway validation test suite
├── test_results_qwen25_120s.log
└── pyproject.toml              # dependencies: litellm>=1.81.5
```

### Active Infrastructure

| Component | Location | Port | Status |
|-----------|----------|------|--------|
| hailo-ollama | system binary | 8000 | ✅ Working (no tools support) |
| Community gateway | `/home/marcomark/Documents/code-projects/ollama_gateway` | 11434 | ✅ Validated (tools supported) |
| Model (gateway) | `~/hailo-models/Qwen2.5-1.5B-Instruct.hef` | — | ✅ Compatible with HailoRT 5.1.1 |

### Starting the Community Gateway

```bash
cd /home/marcomark/Documents/code-projects/ollama_gateway
export HAILO_HEF_PATH=/home/marcomark/hailo-models/Qwen2.5-1.5B-Instruct.hef
source .venv_with_system/bin/activate
python hailo_ollama_gateway.py
```

Then load the model (separate terminal):
```bash
curl -s -X POST http://localhost:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "/home/marcomark/hailo-models/Qwen2.5-1.5B-Instruct.hef"}'
```

Verify it's running:
```bash
curl -s http://localhost:11434/api/tags
```

---

## Long-Term Tool Architecture

The eventual set of tools is designed to represent the full technical breadth of capabilities needed for this hardware/architecture in future projects. The 5 planned tool types are:

| # | Tool Type | Example | Represents |
|---|-----------|---------|------------|
| 1 | Hardcoded local function | `get_current_time()` | Pure local computation |
| 2 | Outbound HTTP request | `get_weather(location)` | External API integration |
| 3 | MQTT message publish | `publish_mqtt_message(topic, payload)` | IoT/edge messaging |
| 4 | AWS Lambda invoke | `invoke_lambda(function_name, payload)` | Serverless compute |
| 5 | Amazon Polly TTS | `text_to_speech(text)` | Cloud AI services / audio output |

This is a prototype to validate the architecture. Tools are intentionally simple — the point is proving each integration pattern works on this hardware stack.

---

## Phase Plan

### Phase 1 — Core Strands Agent + 2 Tools (CURRENT PHASE)
Get a working Strands agent with tool calling validated end-to-end.

**Tools:** `get_current_time` (type 1) + `get_weather` (type 2)

### Phase 2 — Remaining Tools (FUTURE)
Add MQTT, Lambda, and Polly tools once Phase 1 is confirmed working.

### Phase 3 — Polish (FUTURE)
Finalize `main.py` CLI with the Strands agent, update documentation, finalize architecture decisions.

---

## Phase 1 Task List

### Task 1 — Swap dependencies and remove LiteLLM
**Status:** ✅ COMPLETE

**What to do:**
```bash
uv add strands-agents httpx
uv remove litellm
uv sync
```

Then delete the files that depended on LiteLLM:
```bash
rm src/agent_neo/provider.py
rm src/agent_neo/agent.py
```

`strands-agents` is the AWS Strands Agents SDK. `httpx` is for the weather tool HTTP call. `litellm` is removed entirely — Strands is the replacement, not an addition.

**Note on `main.py`:** After deleting `agent.py`, `main.py` will have a broken import (`from .agent import create_agent`) and `uv run agent-neo` will fail. This is expected and acceptable — `main.py` will be rewritten in Task 6. Do not fix `main.py` yet.

**Verify:**
```bash
uv pip list | grep strands
uv pip list | grep httpx
uv pip list | grep litellm   # should return nothing
```

**Expected outcome:** `strands-agents` and `httpx` in installed list. `litellm` absent. `pyproject.toml` reflects new dependencies. `provider.py` and `agent.py` deleted.

**Notes:**
- The project uses UV exclusively (not pip directly)
- Python 3.13.5 on Raspberry Pi 5
- If `strands-agents` installs but imports fail, check for ARM64 compatibility issues

---

### Task 2 — Update config for gateway
**Status:** ✅ COMPLETE

**File to modify:** `src/agent_neo/config.py`

**Replace entire contents with:**
```python
"""Configuration settings for Agent Neo."""

# Community gateway settings
GATEWAY_BASE = "http://localhost:11434"
GATEWAY_MODEL = "hailo-llm"

# Request settings
REQUEST_TIMEOUT = 120.0  # seconds
```

The old `MODEL_ID` and `API_BASE` constants are removed — they referenced hailo-ollama (port 8000) which is no longer used.

**Notes:**
- `hailo-llm` is the model name the gateway registers itself as (confirmed in test results)
- `REQUEST_TIMEOUT` is kept — Strands will use the same 120s timeout

---

### Task 3 — Create `tools.py`
**Status:** ✅ COMPLETE

**File to create:** `src/agent_neo/tools.py`

**Tool 1: `get_current_time`**
- Returns the current local date and time as a formatted string
- No external dependencies
- Should return something like: `"Thursday, 20 February 2026, 14:32:05 GMT+0"`

**Tool 2: `get_weather`**
- Parameter: `location: str` (city name or "city, country")
- Calls `https://wttr.in/{location}?format=j1` (public JSON API, no API key required)
- Returns a brief human-readable summary: temperature (°C), weather condition description
- Timeout: 10 seconds
- Handle errors gracefully — return an error string, don't raise

**Note:** `provider.py` and `agent.py` are already deleted by Task 1. `litellm` is already removed. These tools have no dependency on the old implementation.

**Strands tool definition pattern:**
```python
from strands import tool

@tool
def get_current_time() -> str:
    """Return the current local date and time."""
    ...

@tool
def get_weather(location: str) -> str:
    """Get the current weather for a location. location should be a city name."""
    ...
```

**Notes:**
- The `@tool` decorator is how Strands discovers tools — the docstring becomes the tool description sent to the model
- Tool function signatures should use type hints — Strands uses these to build the JSON schema
- Keep docstrings concise and action-oriented (the model reads them)
- `wttr.in` JSON response key path for current conditions: `response["current_condition"][0]`
  - Temperature: `temp_C`
  - Description: `weatherDesc[0]["value"]`

---

### Task 4 — Create `strands_agent.py`
**Status:** ✅ COMPLETE

**File to create:** `src/agent_neo/strands_agent.py`

**What it does:**
- Instantiates a Strands `Agent` with `OllamaModel` pointing at the community gateway
- Registers `get_current_time` and `get_weather` tools
- Exposes a `chat(message: str)` method that runs the agent and returns/streams the response
- This is the permanent replacement for `agent.py` + `provider.py`, not a parallel implementation

**Key configuration:**
```python
from strands import Agent
from strands.models.ollama import OllamaModel  # verify exact import path
from .config import GATEWAY_BASE, GATEWAY_MODEL
from .tools import get_current_time, get_weather

model = OllamaModel(
    host=GATEWAY_BASE,
    model_id=GATEWAY_MODEL,
)

agent = Agent(
    model=model,
    tools=[get_current_time, get_weather],
    system_prompt="You are Agent Neo, a helpful AI assistant running on a Raspberry Pi with Hailo AI HAT+ 2. Be concise and helpful.",
)
```

**Notes:**
- The exact Strands import paths need to be verified after install (`strands.models.ollama` is the expected path but confirm)
- Do NOT modify `agent.py` or `provider.py` — the LiteLLM agent remains the stable production path
- If `OllamaModel` isn't available, check if Strands supports a generic OpenAI-compatible provider (the gateway also speaks Ollama API format)

---

### Task 5 — Create `chat.py` (standalone test script)
**Status:** ✅ COMPLETE (deleted after cutover as planned)

**File to create:** `src/agent_neo/chat.py` (or at project root if easier to run)

**Purpose:** A minimal interactive chat loop using the new Strands agent. Used for initial validation before replacing `main.py`. Once Task 6 passes, `main.py` will be updated to use the Strands agent and `chat.py` will be removed.

**What it does:**
- Imports `StrandsAgent` from `strands_agent.py`
- Starts a REPL: `You: ` prompt → agent response → repeat
- Supports `quit`/`exit` and `Ctrl+C` to stop
- Prints responses as they stream (if Strands supports streaming callback)

**Run command:**
```bash
uv run python src/agent_neo/chat.py
```

---

### Task 6 — End-to-end test and cutover
**Status:** ✅ COMPLETE

**Prerequisite:** Community gateway must be running (see startup instructions above).

**Test prompts to run manually:**

| Prompt | Expected behavior |
|--------|------------------|
| `"What time is it?"` | Agent calls `get_current_time`, returns current time |
| `"What's the weather in London?"` | Agent calls `get_weather("London")`, returns weather |
| `"What's the weather in Tokyo and what time is it here?"` | Agent calls both tools |
| `"Tell me a joke"` | Agent responds directly, no tool call |

**Pass criteria:**
- Tool calls are actually invoked (not just text response)
- Tool results are incorporated into the final answer
- Conversation is coherent
- No unhandled exceptions

**If tool calls don't fire:**
See the "Known Risk" section below.

**Once tests pass — cutover steps:**
1. Update `main.py` to import and use `StrandsAgent` instead of the now-deleted `AgentNeo`
2. Delete `src/agent_neo/chat.py`
3. Verify `uv run agent-neo` works end-to-end

---

### Task 7 — Update documentation
**Status:** ✅ COMPLETE

**Files to update:**
1. `docs/STEERING.md` — Add a new session entry under "Handoff Notes" with date, what was completed, and what's next
2. `docs/REQUIREMENTS.md` — Document the decision to use Strands + community gateway, note that LiteLLM agent is retained as fallback
3. This file (`docs/STRANDS_INTEGRATION.md`) — Update task statuses and add any new findings

---

## Known Risk: Model Tool-Calling Reliability

**Risk level:** HIGH — confirmed and resolved (2026-02-21)

**What happened:**
`Qwen2.5-1.5B-Instruct` (general instruction model) does not reliably invoke tools. During Task 6 testing it hallucinated responses instead of calling tools, even with explicit prompts. This confirmed the risk documented here.

**Resolution taken: Option B — AWS Bedrock (Claude Haiku)**
Switched `strands_agent.py` to use `BedrockModel` with `us.anthropic.claude-haiku-4-5-20251001-v1:0`. All 4 end-to-end tests passed with correct tool invocation.

**HailoRT upgrade status (2026-02-21): BLOCKED — Python bindings ABI incompatible**

Hardware is fully upgraded and working. Python bindings are the blocker.

Detailed state:
- `hailort 5.2.0` runtime installed (replaces `h10-hailort 5.1.1`)
- `hailort-pcie-driver 5.2.0` installed (DKMS module built and installed)
- 5.2.0 firmware active after reboot: `hailortcli fw-control identify` shows firmware 5.2.0, HAILO10H
- `/dev/hailo0` present
- `python3-h10-hailort 5.1.1` retained; compatibility symlinks created (`/usr/lib/libhailort.so.5.1.1 → /usr/lib/libhailort.so.5.2.0`) — but import still fails
- Rollback debs at `~/Downloads/hailort-5.1.1-backup/`

**Root cause of Python bindings failure (confirmed 2026-02-21):**

The `Speech2TextGeneratorParams` constructor changed its signature between 5.1.1 and 5.2.0 — a `float` parameter (likely `repetition_penalty`) was added. This changes the C++ mangled symbol name:

| Version | Symbol |
|---------|--------|
| 5.1.1 bindings expect | `...Speech2TextGeneratorParamsC1...string_view` |
| 5.2.0 library exports | `...Speech2TextGeneratorParamsC1...string_viewf` (extra `f` = float) |

The compatibility symlink allows the `.so` to load `libhailort`, but cannot invent missing symbols. The Python bindings must be recompiled against 5.2.0.

**`python3-hailort 4.23.0`** (available in apt) is the Hailo-8 product line — not applicable to H10H.

**Paths under investigation:**
1. Build `pyhailort` from source against 5.2.0 headers (requires Hailo GitHub source)
2. Obtain pre-built 5.2.0 bindings from Hailo developer zone
3. User-identified alternatives (TBD)
4. Roll back to 5.1.1 (bindings work, but function-calling HEF model won't load)

**Next steps after reboot** (run in order, stop and report on any failure):

**Step 5 — Verify hardware:**
```bash
hailortcli --version          # must show 5.2.0
hailortcli fw-control identify  # must show Hailo-10H device info, no errors
ls -la /dev/hailo0            # device node must exist
```

**Step 6 — Start gateway with function-calling model and verify:**
```bash
cd /home/marcomark/Documents/code-projects/ollama_gateway
export HAILO_HEF_PATH=/home/marcomark/hailo-models/Qwen2-1.5B-Instruct-Function-Calling-v1.hef
source .venv_with_system/bin/activate
python hailo_ollama_gateway.py &
sleep 5
curl -s http://localhost:11434/api/tags   # must list hailo-llm
```
Stop and report if VDevice() init fails with error code 8 — that means Python bindings ABI incompatibility.

**Step 7 — Confirm existing agent still works (still uses Bedrock):**
```bash
cd /home/marcomark/Documents/code-projects/agent-neo
uv run python -c "
from agent_neo.strands_agent import create_agent
agent = create_agent()
agent('What time is it?')
"
```

**Step 8 — Switch strands_agent.py to OllamaModel** (only after Step 6 passes):

File: `src/agent_neo/strands_agent.py` — replace entire contents with:
```python
"""Strands-based agent for Agent Neo using local Hailo NPU inference."""

from strands import Agent
from strands.models.ollama import OllamaModel

from .config import GATEWAY_BASE, GATEWAY_MODEL, REQUEST_TIMEOUT
from .tools import get_current_time, get_weather

SYSTEM_PROMPT = """You are Agent Neo, a helpful AI assistant running on a Raspberry Pi with the AI HAT+ 2. Be concise and helpful."""


def create_agent() -> Agent:
    """Create and return a configured Strands Agent instance."""
    model = OllamaModel(
        host=GATEWAY_BASE,
        model_id=GATEWAY_MODEL,
        ollama_client_args={"timeout": REQUEST_TIMEOUT},
    )

    return Agent(
        model=model,
        tools=[get_current_time, get_weather],
        system_prompt=SYSTEM_PROMPT,
    )
```

**Step 9 — Re-run all 4 Phase 1 test prompts against local model:**
```
"What time is it?"
"What's the weather in London?"
"What's the weather in Tokyo and what time is it?"
"Tell me a joke"
```
Pass criteria: tool calls fire on local Hailo NPU (verify gateway logs show model activity).

**Step 10 — Update docs and commit** (after Step 9 passes):
- Mark this section resolved in `STRANDS_INTEGRATION.md`
- Add session note to `STEERING.md`
- Remove `BEDROCK_MODEL_ID` constant from `strands_agent.py` (already done in Step 8 above)

---

## Architectural Decisions (This Phase)

| Decision | Rationale |
|----------|-----------|
| Remove LiteLLM in Task 1, not at the end | No reason to carry dead weight through the migration; clean break from the start |
| Use Strands `OllamaModel` | Direct Ollama API — matches gateway's native protocol |
| `chat.py` separate from `main.py` | Isolate new code during testing; deleted after cutover in Task 6 |
| `wttr.in` for weather (no API key) | Simpler setup; appropriate for prototype |
| `httpx` for HTTP in tools | Consistent with project style; avoids `requests` |
| Tools as separate `tools.py` module | Clean separation; tools will grow across phases |

---

## Phase 2 Task List — Remaining Tools

**Status:** 🟡 IN PROGRESS
**Goal:** Add MQTT, Lambda, and Polly tools to complete the prototype tool breadth.

### Phase 2 — Task 1: Install paho-mqtt
**Status:** 🔴 NOT STARTED

```bash
uv add paho-mqtt
```

Verify:
```bash
uv run python -c "import paho.mqtt.client; print('paho-mqtt OK')"
```

`boto3` is already installed (came in with `strands-agents`) — no new packages needed for Lambda or Polly.

---

### Phase 2 — Task 2: Create test Lambda function
**Status:** 🔴 NOT STARTED

A simple test function must be deployed to AWS before the Lambda tool can be tested.

**Function name:** `agent-neo-test`
**Runtime:** Python 3.13
**Region:** `us-east-1`

**Handler code:**
```python
import json

def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "message": f"agent-neo-test received: {json.dumps(event)}"
    }
```

**Deployment steps (via boto3):**
1. Create IAM execution role with `AWSLambdaBasicExecutionRole` policy
2. Zip the handler code
3. Create the Lambda function with the role ARN
4. Wait for `State: Active`
5. Invoke with a test payload to verify

**Notes:**
- IAM user `Mark` (account `130843671546`) needs `lambda:CreateFunction`, `lambda:InvokeFunction`, `iam:CreateRole`, `iam:AttachRolePolicy`, `iam:PassRole`
- If permission errors occur, stop and report — do not attempt workarounds
- Role name: `agent-neo-lambda-role`

---

### Phase 2 — Task 3: Add 3 new tools to `tools.py`
**Status:** 🔴 NOT STARTED

**Tool 3: `publish_mqtt_message`**
- Broker: `test.mosquitto.org` (public, no auth, port 1883)
- Connects, publishes, disconnects — synchronous single-shot pattern
- Returns confirmation string with topic and payload

**Tool 4: `invoke_lambda`**
- Parameters: `function_name: str`, `payload: str` (JSON string)
- Uses `boto3` Lambda client with `InvocationType="RequestResponse"`
- Decodes and returns the response payload
- Timeout: 30 seconds

**Tool 5: `text_to_speech`**
- Parameters: `text: str`, `output_file: str = "speech.mp3"`
- Uses `boto3` Polly client, voice `Joanna`, format `mp3`
- Saves audio to `output_file` path
- Returns the path to the saved file

---

### Phase 2 — Task 4: Register new tools in `strands_agent.py`
**Status:** 🔴 NOT STARTED

Add the 3 new tools to the `tools` list in `create_agent()`.

---

### Phase 2 — Task 5: End-to-end test all 3 new tools
**Status:** 🔴 NOT STARTED

**Test prompts:**

| Prompt | Expected behaviour |
|--------|-------------------|
| `"Publish 'hello from Agent Neo' to the topic agent-neo/test"` | `publish_mqtt_message` called, confirmation returned |
| `"Invoke the agent-neo-test Lambda with the payload hello world"` | `invoke_lambda` called, Lambda response returned |
| `"Say 'Hello, I am Agent Neo' using text to speech"` | `text_to_speech` called, `speech.mp3` saved, path returned |

**Pass criteria:**
- Each tool is invoked (not hallucinated)
- MQTT: no connection errors from `test.mosquitto.org`
- Lambda: response payload decoded and returned
- Polly: `speech.mp3` file exists and is non-zero bytes

---

### Phase 2 — Task 6: Update documentation
**Status:** 🔴 NOT STARTED

Update `STEERING.md` session notes and task statuses in this file.

---

## Quick Reference for New Sessions

**What we're building:** Strands-based agent with tool calling on Raspberry Pi + Hailo NPU

**Current status:** Phase 1 complete. Phase 2 in progress (5 tools total: time, weather, MQTT, Lambda, Polly).

**Approach philosophy (from STEERING.md):**
- Ask permission before modifying code
- Work one task at a time, test before moving on
- Stop and report if a blocker is hit — do not attempt workarounds

**Run agent:**
```bash
uv run agent-neo
```

---

*Last updated: 2026-02-20 — Plan created, no tasks started.*
