"""Test script for the Direct Hailo Provider integration with Strands Agent."""

import asyncio
import logging

from agent_neo.strands_agent import create_agent

# Configure logging to see the flow
logging.basicConfig(level=logging.INFO)


async def main():
    print("--- Testing Direct Hailo Provider (Mock Inference) ---")
    agent = create_agent()

    # Test 1: Simple greeting (no tool call)
    print("\n[PROMPT] Hello")
    response = await agent.invoke_async("Hello")
    print(f"[RESPONSE DEBUG] {response}")

    # Test 2: Current time (simulated tool call)
    print("\n[PROMPT] What time is it?")
    response = await agent.invoke_async("What time is it?")
    print(f"[RESPONSE DEBUG] {response}")


if __name__ == "__main__":
    asyncio.run(main())
