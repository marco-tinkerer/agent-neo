"""Strands-based agent for Agent Neo using direct Hailo NPU inference."""

from strands import Agent

from .config import HEF_PATH
from .models import HailoModel
from .tools import get_current_time, get_weather

SYSTEM_PROMPT = """You are Agent Neo, a helpful AI assistant running on a Raspberry Pi with the AI HAT+ 2. Be concise and helpful."""


def create_agent() -> Agent:
    """Create and return a configured Strands Agent instance using HailoModel."""
    model = HailoModel(hef_path=HEF_PATH)

    return Agent(
        model=model,
        tools=[get_current_time, get_weather],
        system_prompt=SYSTEM_PROMPT,
    )
