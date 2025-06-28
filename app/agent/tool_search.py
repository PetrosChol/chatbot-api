import logging
from app.agent.client import get_instructor_client 
from app.agent.schemas import ResponseSchema
from app.utils.current_date import current_date
from app.utils.current_week import current_week
from app.agent.prompts.tools_system_prompt import tools_system_prompt
from app.agent.prompts.tools_user_prompt import (
    tools_user_prompt,
)

logger = logging.getLogger(__name__)


async def search_for_tools(
    user_message: str,
    history: list,
) -> ResponseSchema:
    """
    Analyzes the user message and history using an LLM to determine if tools
    are needed, clarification is required, or a direct response is appropriate.

    Args:
        user_message: The latest message from the user.
        history: The recent conversation history (list of message dicts).

    Returns:
        A ResponseSchema object indicating the next step.
    """
    client = get_instructor_client()

    # Format history for the prompt
    # Newest messages are typically at the end of the history list from Redis
    formatted_history = "\n".join(
        [f"{msg['type']}: {msg['message']}" for msg in history]
    )

    # Format the user prompt by replacing placeholders
    formatted_user_prompt = (
        tools_user_prompt.replace("{{current_date}}", current_date())
        .replace("{{current_week}}", current_week())
        .replace("{{formatted_history}}", formatted_history)
        .replace("{{user_message}}", user_message)
    )

    messages_for_api = [
        {"role": "system", "content": tools_system_prompt},
        {"role": "user", "content": formatted_user_prompt},
    ]

    try:
        response = await client.chat.completions.create(
            messages=messages_for_api,
            response_model=ResponseSchema,
        )
        return response
    except Exception as e:
        logger.error(f"Error calling LLM for tool search: {e}", exc_info=True)
        # Fallback: return a default response asking for clarification or indicating an error
        # This prevents the agent from getting stuck if the LLM call fails
        return ResponseSchema(
            reasoning="Failed to analyze the request due to an internal error. Could not determine the required tools.",
            direct_response="I encountered an issue trying to understand your request. Could you please rephrase it?",
        )
