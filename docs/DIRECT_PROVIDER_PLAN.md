# Direct Hailo Provider: Architecture & Build Plan

**Date:** March 7, 2026
**Status:** PROPOSED
**Prepared by:** Gemini CLI

---

## 1. Analysis: Transitioning from Gateway to Direct Provider

### 1.1 The Current "Gateway" Architecture
The current design uses a standalone FastAPI server (`ollama_gateway`) as a "Hardware Bridge" between the Strands Agent and the Hailo NPU. This was a necessary first step to bypass the API limitations of the official `hailo-ollama` server.

**Challenges with the Gateway:**
*   **Latency Overhead:** Every request must traverse the HTTP stack (JSON serialization, socket overhead, etc.).
*   **Reliability Issues:** Non-streaming requests consistently time out (120s limit) because they are treated as synchronous blocks.
*   **Dependency Fragmentation:** The gateway requires its own virtual environment and model-loading logic, making the system harder to manage and deploy as a single unit.

### 1.2 The "Direct Provider" Solution
By implementing a custom `HailoModel` directly within the Strands Agents SDK, we can bypass the network layer entirely and run inference in the same process as the Agent.

**Key Benefits:**
*   **Zero-Network Overhead:** Direct communication with the `hailo_platform` via Python C-bindings.
*   **Lifecycle Control:** The Agent can manage the NPU's power state (`VDevice`) and model loading (`HEF`) directly.
*   **Simplified Deployment:** One environment, one process, one configuration.

---

## 2. Technical Decision

**Decision:** Rebuild the Agent Neo environment to support system-level drivers and implement a custom Strands `Model` provider for the Hailo NPU.

**Architectural Change:**
*   **FROM:** `Agent` -> `Strands OllamaModel` -> `HTTP (Port 11434)` -> `Ollama Gateway` -> `HailoRT`
*   **TO:** `Agent` -> `Strands HailoModel` -> `HailoRT (Direct C-Bindings)`

---

## 3. Build Plan

### Phase 1: Environment Alignment
To allow the `uv` environment to access the Hailo hardware drivers installed at the system level (`/usr/lib/python3/dist-packages`), we must rebuild the virtual environment with system-site-package access.

1.  **Backup:** Ensure `uv.lock` and `pyproject.toml` are current.
2.  **Rebuild:** 
    ```bash
    rm -rf .venv
    uv venv --system-site-packages
    uv sync
    ```
3.  **Verification:** Confirm `import hailo_platform` works within the new environment.

### Phase 2: `HailoModel` Implementation
Create a new module `src/agent_neo/models/hailo.py` that implements the `strands.models.Model` interface.

**Key Components:**
*   **Inference Engine:** Wrap the `hailo_platform.HEF` loading and `VDevice` initialization.
*   **Prompt Alignment:** Small local models (1.5B - 3B) fail with the default Strands prompts. We will implement model-specific templates for **Qwen2.5-Instruct** or **Llama 3.2-3B**.
*   **Streaming Output Repair:** A specialized parser will "clean" the raw model output in real-time, extracting tool calls even if the model produces malformed JSON or unnecessary conversational filler.

### Phase 3: Validation & Cleanup
1.  **Phase 1 Tests:** Re-run the Time/Weather tool tests using the new `HailoModel`.
2.  **Performance Benchmark:** Compare latency between the Direct Provider and the old Gateway (expecting >50% improvement in time-to-first-token).
3.  **Decommissioning & Cleanup:**
    *   **Internal Files:** Delete `test_gateway.py` and all `test_results_*.log` files from the project root.
    *   **Dependencies:** Run `uv remove ollama` to strip out the legacy Ollama API client.
    *   **External (Manual):** The user should manually delete the `/home/marcomark/Documents/code-projects/ollama_gateway` directory, as it resides outside this workspace.
    *   **Documentation:** Update `STRANDS_INTEGRATION.md` and `REQUIREMENTS.md` to reflect the shift from "Gateway-based" to "Direct-integrated" architecture.

---

## 4. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **VDevice Resource Locking** | Implement a robust `__del__` and `atexit` handler to ensure the NPU is released even if the process crashes. |
| **Memory Fragmentation** | Monitor the RPi 5's RAM; small models (1.5B) are light, but loading multiple HEFs could be an issue. |
| **Model Hallucination** | Use "Few-Shot" prompting within the `HailoModel` to force the local model into the correct JSON format for tools. |

---

## 5. Next Steps
1.  User review and approval of this plan.
2.  Execution of **Phase 1 (Environment Rebuild)**.
3.  Initial scaffolding of the `HailoModel` provider.
