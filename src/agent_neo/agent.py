"""Agent Neo - Simple conversational agent powered by LiteLLM."""

from .provider import LiteLLMProvider

SYSTEM_PROMPT = """You are Agent Neo, a helpful AI assistant running on a Raspberry Pi with the AI HAT+ 2. Be concise and helpful."""


class AgentNeo:
    """A simple conversational agent powered by LiteLLM.

    Maintains conversation history and provides a chat interface
    to the local LLM.
    """

    def __init__(
        self,
        system_prompt: str = SYSTEM_PROMPT,
        stream: bool = True,
    ) -> None:
        """Initialize the agent.

        Args:
            system_prompt: The system prompt for the agent.
            stream: Whether to stream responses (shows text as it generates).
        """
        self.client = LiteLLMProvider()
        self.system_prompt = system_prompt
        self.stream = stream
        self.conversation: list[dict] = []

    def chat(self, message: str) -> str:
        """Send a message and get a response.

        Args:
            message: The user's message.

        Returns:
            The assistant's response.
        """
        if self.stream:
            response_parts = []
            for chunk in self.client.chat_stream(
                message,
                conversation=self.conversation,
                system_prompt=self.system_prompt,
            ):
                print(chunk, end="", flush=True)
                response_parts.append(chunk)
            print()  # Newline after streaming
            response = "".join(response_parts)
        else:
            response = self.client.chat(
                message,
                conversation=self.conversation,
                system_prompt=self.system_prompt,
            )

        # Update conversation history
        self.conversation.append({"role": "user", "content": message})
        self.conversation.append({"role": "assistant", "content": response})

        return response

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation = []


def create_agent(stream: bool = True) -> AgentNeo:
    """Create and return an AgentNeo instance.

    Args:
        stream: Whether to stream responses.

    Returns:
        A configured AgentNeo instance.
    """
    return AgentNeo(stream=stream)
