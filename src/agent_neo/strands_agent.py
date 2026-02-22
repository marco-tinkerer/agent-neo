"""Strands-based agent for Agent Neo.

Currently uses AWS Bedrock (Claude Haiku) as the model backend while
HailoRT is upgraded to 5.2.0 to support the function-calling HEF model.
Once HailoRT 5.2.0 is available, swap BedrockModel for OllamaModel
pointing at the community gateway (see config.py for gateway settings).
"""

from strands import Agent
from strands.models import BedrockModel

from .tools import get_current_time, get_weather

SYSTEM_PROMPT = """You are Agent Neo, a helpful AI assistant running on a Raspberry Pi with the AI HAT+ 2. Be concise and helpful."""

# Claude Haiku on Bedrock — fast and cost-efficient for tool-calling validation
BEDROCK_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


def create_agent() -> Agent:
    """Create and return a configured Strands Agent instance."""
    model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name="us-east-1",
    )

    return Agent(
        model=model,
        tools=[get_current_time, get_weather],
        system_prompt=SYSTEM_PROMPT,
    )
