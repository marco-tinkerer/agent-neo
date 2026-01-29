"""Main entry point for Agent Neo."""

from .agent import create_agent


def main() -> None:
    """Run the Agent Neo interactive loop."""
    print("Agent Neo - Powered by hailo-ollama on Raspberry Pi AI HAT+ 2")
    print("Type 'quit' or 'exit' to end the conversation.")
    print("Type 'clear' to clear conversation history.\n")

    agent = create_agent(stream=True)

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit"):
                print("Goodbye!")
                break

            if user_input.lower() == "clear":
                agent.clear_history()
                print("Conversation history cleared.\n")
                continue

            print("Agent Neo: ", end="", flush=True)
            agent.chat(user_input)
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
