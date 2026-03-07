"""Main entry point for Agent Neo."""

import asyncio
import sys

from agent_neo.strands_agent import create_agent


async def async_main():
    """Asynchronous main loop for the agent."""
    print("Welcome to Agent Neo (Direct NPU Integration)")
    print("Type 'exit' or 'quit' to stop.")
    
    agent = create_agent()
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                break
            
            if not user_input:
                continue
                
            response = await agent.invoke_async(user_input)
            print(f"\nNeo: {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError: {e}")

    print("\nGoodbye!")


def main():
    """Synchronous entry point."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
