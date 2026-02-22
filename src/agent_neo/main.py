"""Main entry point for Agent Neo."""

from .strands_agent import create_agent


def main() -> None:
    """Run the Agent Neo interactive loop."""
    print("Agent Neo - Powered by Strands on Raspberry Pi AI HAT+ 2")
    print("Type 'quit' or 'exit' to end the conversation.\n")

    agent = create_agent()

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit"):
                print("Goodbye!")
                break

            print("Agent Neo: ", end="", flush=True)
            agent(user_input)
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
