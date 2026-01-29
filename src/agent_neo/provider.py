"""LLM provider using LiteLLM.

Provides a unified interface to communicate with LLMs via LiteLLM,
supporting multiple backends (Ollama, Bedrock, etc.).
"""

from collections.abc import Iterator

import litellm

from .config import API_BASE, MODEL_ID, REQUEST_TIMEOUT


class LiteLLMProvider:
    """LLM provider using LiteLLM for model access.

    Wraps litellm.completion() to provide chat and streaming chat methods.
    """

    def __init__(
        self,
        model: str = MODEL_ID,
        api_base: str = API_BASE,
        timeout: float = REQUEST_TIMEOUT,
    ) -> None:
        """Initialize the provider.

        Args:
            model: The LiteLLM model identifier (e.g. "ollama/qwen2:1.5b").
            api_base: The API base URL.
            timeout: Request timeout in seconds.
        """
        self.model = model
        self.api_base = api_base
        self.timeout = timeout

    def _build_messages(
        self,
        message: str,
        conversation: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> list[dict]:
        """Build the messages list for a completion request."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if conversation:
            messages.extend(conversation)
        messages.append({"role": "user", "content": message})
        return messages

    def chat(
        self,
        message: str,
        conversation: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """Send a chat message and get a response.

        Args:
            message: The user's message.
            conversation: Optional conversation history.
            system_prompt: Optional system prompt.

        Returns:
            The assistant's response text.
        """
        messages = self._build_messages(message, conversation, system_prompt)
        response = litellm.completion(
            model=self.model,
            api_base=self.api_base,
            messages=messages,
            stream=False,
            timeout=self.timeout,
        )
        return response.choices[0].message.content

    def chat_stream(
        self,
        message: str,
        conversation: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """Send a chat message and stream the response.

        Args:
            message: The user's message.
            conversation: Optional conversation history.
            system_prompt: Optional system prompt.

        Yields:
            Response text chunks as they arrive.
        """
        messages = self._build_messages(message, conversation, system_prompt)
        response = litellm.completion(
            model=self.model,
            api_base=self.api_base,
            messages=messages,
            stream=True,
            timeout=self.timeout,
        )
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content
