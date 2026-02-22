"""Tool definitions for Agent Neo.

Tools are registered with the Strands agent via the @tool decorator.
The function docstring is sent to the model as the tool description.
"""

from datetime import datetime

import httpx

from strands import tool


@tool
def get_current_time() -> str:
    """Return the current local date and time."""
    return datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")


@tool
def get_weather(location: str) -> str:
    """Get the current weather for a location.

    Args:
        location: City name, e.g. 'London' or 'Tokyo, Japan'.
    """
    try:
        response = httpx.get(
            f"https://wttr.in/{location}?format=j1",
            timeout=10.0,
            headers={"User-Agent": "agent-neo/0.1"},
        )
        response.raise_for_status()
        data = response.json()
        condition = data["current_condition"][0]
        temp_c = condition["temp_C"]
        description = condition["weatherDesc"][0]["value"]
        feels_like = condition["FeelsLikeC"]
        return f"{location}: {description}, {temp_c}°C (feels like {feels_like}°C)"
    except httpx.TimeoutException:
        return f"Weather request timed out for '{location}'."
    except httpx.HTTPStatusError as e:
        return f"Weather service returned an error: {e.response.status_code}."
    except (KeyError, ValueError):
        return f"Could not parse weather data for '{location}'."
    except httpx.RequestError as e:
        return f"Could not reach weather service: {e}."
