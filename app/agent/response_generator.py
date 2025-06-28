import logging
from app.agent.client import get_instructor_client
from app.agent.schemas import FinalResponseSchema
from app.utils.current_week import current_week
from app.utils.current_datetime import current_datetime
from app.agent.prompts.synthesizer_system_prompt import (
    synthesizer_system_prompt,
)
from app.agent.prompts.synthesizer_user_prompt import (
    synthesizer_user_prompt,
) 

logger = logging.getLogger(__name__)


async def get_response_with_db_info_grounding(
    user_message: str,
    history: list,
    tool_results: dict,
) -> FinalResponseSchema:
    """
    Generates the final user-facing response using the user message, history,
    and results retrieved from tools (database queries, etc.).

    Args:
        user_message: The original user message that triggered the tool use.
        history: The recent conversation history.
        tool_results: A dictionary containing the results from executed tools.
                      Keys are tool names, values are results or error messages.

    Returns:
        A FinalResponseSchema object containing the reasoning and final response.
    """
    client = get_instructor_client()

    # Format history and tool results for the prompt
    formatted_history = "\n".join(
        [f"{msg['type']}: {msg['message']}" for msg in history]
    )
    formatted_tool_results = str(tool_results)

    # Format the user prompt by replacing placeholders
    formatted_user_prompt = (
        synthesizer_user_prompt.replace("{{current_datetime}}", current_datetime())
        .replace("{{current_week}}", current_week())
        .replace("{{chat_history}}", formatted_history)
        .replace("{{content}}", formatted_tool_results)
        .replace("{{user_message}}", user_message)
    )

    messages_for_api = [
        {
            "role": "system",
            "content": synthesizer_system_prompt,
        },
        {
            "role": "user",
            "content": formatted_user_prompt,
        },    ]

    try:
        response = await client.chat.completions.create(
            messages=messages_for_api,
            response_model=FinalResponseSchema,
        )
        return response
    except Exception as e:
        logger.error(f"Error calling LLM for response synthesis: {e}", exc_info=True)
        # Fallback: return a generic error message to the user
        return FinalResponseSchema(
            reasoning="Failed to synthesize a response due to an internal error after retrieving information.",
            response_to_user="I found some information, but encountered an issue while putting together the final response. Please try again.",
        )
