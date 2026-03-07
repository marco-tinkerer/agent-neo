"""Direct Hailo NPU model provider for Agent Neo."""

import json
import logging
import re
from typing import Any, AsyncGenerator, AsyncIterable, TypeVar, override

from strands.models.model import (
    Messages,
    Model,
    StreamEvent,
    ToolChoice,
    ToolSpec,
)
from strands.models.ollama import StopReason

# Attempt to import hailo_platform (should be available via system-site-packages)
try:
    import hailo_platform
    from hailo_platform import HEF, VDevice
except ImportError:
    hailo_platform = None
    HEF = None
    VDevice = None

T = TypeVar("T")

logger = logging.getLogger(__name__)


class RepairingParser:
    """Parses and repairs streaming text from the model, detecting tool calls."""

    def __init__(self):
        self.buffer = ""
        self.in_tool_call = False
        self.current_tool_name = ""
        self.current_tool_args = ""
        
        # Patterns for detecting tool calls in Qwen2-Instruct
        # Example: <tool_call>{"name": "get_weather", "arguments": {"location": "London"}}</tool_call>
        self.tool_start_pattern = re.compile(r"<tool_call>")
        self.tool_end_pattern = re.compile(r"</tool_call>")

    def process_chunk(self, chunk: str) -> list[dict[str, Any]]:
        """Process a text chunk and return a list of events."""
        events = []
        self.buffer += chunk

        while self.buffer:
            if not self.in_tool_call:
                # Look for tool start
                match = self.tool_start_pattern.search(self.buffer)
                if match:
                    # Text before tool call
                    text_before = self.buffer[:match.start()]
                    if text_before:
                        events.append({"type": "text", "content": text_before})
                    
                    self.in_tool_call = True
                    self.buffer = self.buffer[match.end():]
                else:
                    # No tool start found, yield all but maybe a small tail (to not break the tag)
                    if len(self.buffer) > 20:
                        events.append({"type": "text", "content": self.buffer[:-15]})
                        self.buffer = self.buffer[-15:]
                    break
            else:
                # Inside tool call, look for end
                match = self.tool_end_pattern.search(self.buffer)
                if match:
                    tool_json_str = self.buffer[:match.start()].strip()
                    try:
                        tool_call = json.loads(tool_json_str)
                        events.append({"type": "tool", "data": tool_call})
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse tool call JSON: %s", tool_json_str)
                        # Fallback: maybe just treat it as text if it's broken
                        events.append({"type": "text", "content": f"<tool_call>{tool_json_str}</tool_call>"})
                    
                    self.in_tool_call = False
                    self.buffer = self.buffer[match.end():]
                else:
                    # Tool call not finished yet
                    break
        
        return events

    def flush(self) -> list[dict[str, Any]]:
        """Flush remaining buffer."""
        events = []
        if self.buffer:
            if self.in_tool_call:
                # Unfinished tool call, try to parse what we have or just treat as text
                try:
                    # Sometimes models forget the closing tag but produce valid JSON
                    tool_call = json.loads(self.buffer.strip())
                    events.append({"type": "tool", "data": tool_call})
                except json.JSONDecodeError:
                    events.append({"type": "text", "content": f"<tool_call>{self.buffer}"})
            else:
                events.append({"type": "text", "content": self.buffer})
        self.buffer = ""
        return events


class HailoModel(Model):
    """Strands Model provider for Hailo NPU."""

    def __init__(self, hef_path: str, **model_config: Any):
        self.hef_path = hef_path
        self.config = model_config
        self.vdevice = None
        self.infer_model = None
        self._initialized = False

    def _initialize(self):
        if self._initialized:
            return
        
        if not hailo_platform:
            raise RuntimeError("hailo_platform not installed or accessible.")
            
        logger.info("Initializing Hailo VDevice with HEF: %s", self.hef_path)
        self.vdevice = VDevice()
        self.hef = HEF(self.hef_path)
        
        self._initialized = True

    @override
    def update_config(self, **model_config: Any) -> None:
        self.config.update(model_config)

    @override
    def get_config(self) -> Any:
        return self.config

    @override
    async def structured_output(
        self, output_model: type[T], prompt: Messages, system_prompt: str | None = None, **kwargs: Any
    ) -> AsyncGenerator[dict[str, T | Any], None]:
        # Minimal implementation for interface completeness
        raise NotImplementedError("structured_output is not yet implemented for HailoModel")

    @override
    async def stream(
        self,
        messages: Messages,
        tool_specs: list[ToolSpec] | None = None,
        system_prompt: str | None = None,
        *,
        tool_choice: ToolChoice | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamEvent]:
        # warn_on_tool_choice_not_supported(tool_choice)
        self._initialize()

        logger.debug("Formatting request for Hailo NPU")
        prompt = self._format_prompt(messages, tool_specs, system_prompt)
        
        yield self.format_chunk({"chunk_type": "message_start"})
        
        parser = RepairingParser()
        tool_requested = False

        # In a real implementation, we would call the Hailo NPU here.
        # For this phase, we use a mock to verify the Strands integration.
        async for text_chunk in self._run_inference_mock(prompt):
            for event in parser.process_chunk(text_chunk):
                if event["type"] == "text":
                    yield self.format_chunk({"chunk_type": "content_start", "data_type": "text"})
                    yield self.format_chunk({"chunk_type": "content_delta", "data_type": "text", "data": event["content"]})
                    yield self.format_chunk({"chunk_type": "content_stop", "data_type": "text"})
                elif event["type"] == "tool":
                    yield self.format_chunk({"chunk_type": "content_start", "data_type": "tool", "data": event["data"]})
                    yield self.format_chunk({"chunk_type": "content_delta", "data_type": "tool", "data": event["data"]})
                    yield self.format_chunk({"chunk_type": "content_stop", "data_type": "tool", "data": event["data"]})
                    tool_requested = True

        for event in parser.flush():
            if event["type"] == "text":
                yield self.format_chunk({"chunk_type": "content_start", "data_type": "text"})
                yield self.format_chunk({"chunk_type": "content_delta", "data_type": "text", "data": event["content"]})
                yield self.format_chunk({"chunk_type": "content_stop", "data_type": "text"})
            elif event["type"] == "tool":
                yield self.format_chunk({"chunk_type": "content_start", "data_type": "tool", "data": event["data"]})
                yield self.format_chunk({"chunk_type": "content_delta", "data_type": "tool", "data": event["data"]})
                yield self.format_chunk({"chunk_type": "content_stop", "data_type": "tool", "data": event["data"]})
                tool_requested = True

        yield self.format_chunk({"chunk_type": "message_stop", "data": "tool_use" if tool_requested else "end_turn"})

    async def _run_inference_mock(self, prompt: str) -> AsyncGenerator[str, None]:
        """Mock inference for testing the pipeline."""
        # Split prompt to find the last role
        # Simple check: is the last message an assistant message already containing a tool call?
        # A more robust check for a mock: only call tool if the prompt ends with a user message.
        
        last_turn = prompt.strip().split("<|im_start|>")[-1]
        
        if "assistant" in last_turn:
            # If the assistant is already speaking, just finish the thought
            response = "The weather in London is quite pleasant today."
        elif "weather" in prompt.lower():
            response = "I will check the weather for you. <tool_call>{\"name\": \"get_weather\", \"arguments\": {\"location\": \"London\"}}</tool_call>"
        elif "time" in prompt.lower():
            response = "Checking the time... <tool_call>{\"name\": \"get_current_time\", \"arguments\": {}}</tool_call>"
        else:
            response = "Hello! I am Agent Neo running directly on your Raspberry Pi NPU."
            
        # Yield in small chunks to test streaming/buffering
        chunk_size = 5
        for i in range(0, len(response), chunk_size):
            yield response[i : i + chunk_size]

    def _format_prompt(self, messages: Messages, tool_specs: list[ToolSpec] | None = None, system_prompt: str | None = None) -> str:
        """Format the full prompt string for the model."""
        # This will be refined to match Qwen2/Llama 3.2 specific templates
        full_prompt = ""
        if system_prompt:
            full_prompt += f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            
        if tool_specs:
            full_prompt += "You have access to the following tools:\n"
            full_prompt += json.dumps(tool_specs, indent=2)
            full_prompt += "\nTo call a tool, use: <tool_call>{\"name\": \"...\", \"arguments\": {...}}</tool_call>\n"

        for msg in messages:
            role = msg["role"]
            content = "".join([c.get("text", "") for c in msg["content"] if "text" in c])
            full_prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
        
        full_prompt += "<|im_start|>assistant\n"
        return full_prompt

    def format_chunk(self, event: dict[str, Any]) -> StreamEvent:
        """Standardized chunk formatting (copied from OllamaModel for consistency)."""
        match event["chunk_type"]:
            case "message_start":
                return {"messageStart": {"role": "assistant"}}

            case "content_start":
                if event["data_type"] == "text":
                    return {"contentBlockStart": {"start": {}}}
                
                tool_name = event["data"].get("name") or event["data"].get("function", {}).get("name")
                return {"contentBlockStart": {"start": {"toolUse": {"name": tool_name, "toolUseId": tool_name}}}}

            case "content_delta":
                if event["data_type"] == "text":
                    return {"contentBlockDelta": {"delta": {"text": event["data"]}}}
                
                tool_arguments = event["data"].get("arguments") or event["data"].get("function", {}).get("arguments")
                return {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(tool_arguments)}}}}

            case "content_stop":
                return {"contentBlockStop": {}}

            case "message_stop":
                reason: StopReason = "end_turn"
                if event["data"] == "tool_use":
                    reason = "tool_use"
                return {"messageStop": {"stopReason": reason}}

            case _:
                raise RuntimeError(f"chunk_type=<{event['chunk_type']} | unknown type")
