# Slack Integration Design for Agent Neo

## Overview
This document outlines the design for an optional Slack integration feature for Agent Neo. The goal is to enable users to interact with the agent via a Slack bot in private, invite-only workspaces. This extends the agent's conversational capabilities beyond the command-line interface (CLI), allowing remote, team-based interactions while maintaining the agent's core functionality (e.g., LiteLLM-powered responses, conversation history).

This feature is **optional** and non-disruptive to the existing CLI mode. It will be implemented as a new run mode (e.g., `--slack`) in `main.py`, requiring additional dependencies and configuration.

## Motivation
- **User Accessibility**: Allows interaction via Slack for users who prefer a familiar chat interface over CLI, especially for remote or team collaboration.
- **Privacy Fit**: Supports private invites, aligning with preferences for controlled access (no public discovery).
- **Extensibility**: Leverages Slack's API for rich features like threading, file attachments, and channel-based conversations, while keeping the agent lightweight on the Raspberry Pi.
- **Cost-Effectiveness**: No per-message fees like SMS; free for basic Slack usage.

## Requirements
### Functional Requirements
- Users can send messages to the bot in Slack channels or direct messages (DMs).
- The bot responds with Agent Neo's LLM-generated replies, maintaining per-user conversation history.
- Support basic commands (e.g., "clear" to reset history, "quit" equivalent via message).
- Handle multiple users concurrently without interfering with CLI usage.
- Responses should be non-streaming (suitable for chat) and respect Slack's message limits.

### Non-Functional Requirements
- **Performance**: Minimal overhead on Raspberry Pi; responses within reasonable latency (e.g., &lt;10s for typical queries).
- **Security**: Use Slack's bot tokens and signing secrets; validate events to prevent spoofing.
- **Compatibility**: Works with existing dependencies (e.g., LiteLLM, uv); no changes to core agent logic.
- **Privacy**: Invite-only workspaces; no logging of sensitive user data beyond necessary (e.g., Slack user IDs for history).

### Dependencies
- New Python packages: `slack-sdk`, `slack-bolt` (add to `pyproject.toml`).
- Slack account and app setup (free tier sufficient).

## Architecture
### High-Level Design
- **New Components**:
  - `src/agent_neo/slack_agent.py`: Handles Slack bot logic, event listening, and agent instantiation.
  - `src/agent_neo/sms_server.py` (renamed or extended to `web_server.py`?): Could be generalized for web-based modes, but Slack can be standalone.
- **Integration with Existing Code**:
  - Reuse `AgentNeo` class with `stream=False` for responses.
  - Extend `config.py` for Slack credentials.
  - Modify `main.py` to support `--slack` flag for bot mode.
- **Data Flow**:
  1. User sends message in Slack.
  2. Slack Bolt app receives event, extracts user ID and text.
  3. Instantiate or retrieve `AgentNeo` instance per user ID.
  4. Process message via `chat()` method.
  5. Send response back via Slack API.

### Conversation Management
- Use a dictionary (`agents = {user_id: AgentNeo}`) to maintain separate histories per Slack user.
- Commands: Interpret "clear" as `clear_history()`; ignore or respond to "quit" (since Slack is persistent).

### Error Handling
- If LLM fails (e.g., timeout), send fallback message: "Sorry, I'm having trouble responding right now."
- Log errors to console/file without exposing to users.

## Implementation Steps
1. **Setup Slack App**:
   - Create app at api.slack.com.
   - Enable bot scope (e.g., `channels:history`, `im:history`, `chat:write`).
   - Generate bot token and signing secret.

2. **Update Config**:
   - Add to `config.py`:
     ```python
     SLACK_BOT_TOKEN = "xoxb-your-token"
     SLACK_SIGNING_SECRET = "your-secret"
     SLACK_PORT = 5000  # Reuse or separate port
     ```

3. **Code Changes**:
   - Install dependencies: `uv add slack-sdk slack-bolt`.
   - Create `slack_agent.py` as outlined in discussion.
   - Update `main.py` for `--slack` mode.

4. **Testing**:
   - Run locally with ngrok for webhook exposure.
   - Invite bot to private workspace; test DMs and channels.
   - Verify history persistence and commands.

5. **Deployment**:
   - Ensure Pi has internet; run as service if needed.
   - Document in README.md.

## Risks and Mitigations
- **Overhead**: Slack polling/API calls could strain Pi; mitigate by limiting concurrent users.
- **API Limits**: Slack has rate limits; use Bolt's built-in handling.
- **Security**: Rotate tokens regularly; avoid hardcoding.
- **Maintenance**: If Slack API changes, update SDK.

## Future Enhancements
- Support file uploads (e.g., images for vision models if added).
- Integrate with GitHub for notifications (e.g., PR updates).
- Multi-channel support or admin commands.

This design keeps the feature modular and aligned with Agent Neo's architecture. Feedback welcome!
