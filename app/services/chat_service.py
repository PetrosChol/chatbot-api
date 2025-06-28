import uuid
import logging
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory import service as memory_service
from app.agent.tool_search import search_for_tools
from app.agent.response_generator import get_response_with_db_info_grounding
from app.tools.sequential_tool_executor import execute_tools_sequentially
from app.utils.user_query_preprocess import user_query_preprocess

logger = logging.getLogger(__name__)


async def process_chat_message(
    user_message: str,
    session_id: str | None,
    redis_client: redis.Redis,
    db: AsyncSession,
) -> tuple[str, str]:
    """
    Processes the user message, generates a bot reply, and uses the
    memory service to store the conversation turn.
    """

    if session_id is None:
        session_id = str(uuid.uuid4())
        logger.info(f"New session started: {session_id}")

    history = []
    try:
        # Use the get_chat_history from app.memory.service
        # Limit history context sent to models (e.g., last 20 messages = 10 turns)
        history = await memory_service.get_chat_history(
            session_id=session_id,
            redis_client=redis_client,
            limit=4,
        )
        logger.debug(
            f"Loaded {len(history)} history messages for context (Session: {session_id})"
        )
    except Exception as e:
        logger.error(
            f"Failed to get chat history for session {session_id}: {e}", exc_info=True
        )
        # Proceed without history if Redis fails

    logger.info(
        f"Received original user message (length: {len(user_message)}). (Session: {session_id})"
    )
    # Preprocess the user message
    preprocessed_user_message = user_query_preprocess(user_message)
    logger.info(
        f"Preprocessed user message (length: {len(preprocessed_user_message)}). (Session: {session_id})"
    )

    # 1. Determine if tools are needed or if a direct response is appropriate
    search_for_tools_response = await search_for_tools(
        user_message=preprocessed_user_message,
        history=history,
    )
    # Log the type of response and tool names/args if DEBUG, otherwise just a summary
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            f"Tool search response (Session: {session_id}): {search_for_tools_response}"
        )
    else:
        tool_names = (
            [tool.name for tool in search_for_tools_response.tools]
            if search_for_tools_response.tools
            else "None"
        )
        logger.info(
            f"Tool search decision. Direct response: {bool(search_for_tools_response.direct_response)}. Tools: {tool_names}. (Session: {session_id})"
        )

    # Check if the response schema indicates a direct response is available
    if search_for_tools_response.direct_response:
        bot_reply = search_for_tools_response.direct_response
        logger.info(
            f"Direct response generated (length: {len(bot_reply)}). (Session: {session_id})"
        )
    else:
        tool_names_for_log = [tool.name for tool in search_for_tools_response.tools]
        logger.info(
            f"Tools identified for execution: {tool_names_for_log} (Session: {session_id})."
        )
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Tool arguments: {search_for_tools_response.tools} (Session: {session_id})"
            )

        # 2. Execute the identified tools sequentially
        # Use execute_tools_sequentially instead of map_tools/query_db
        tool_results = await execute_tools_sequentially(
            tool_calls=search_for_tools_response.tools, 
            db=db,
        )
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Tool execution results (Session: {session_id}): {tool_results}"
            )
        else:
            # Log summary of tool results, e.g., keys and types or lengths
            tool_results_summary = {
                k: (
                    type(v).__name__
                    if not isinstance(v, (list, dict))
                    else f"{type(v).__name__} of length {len(v)}"
                )
                for k, v in tool_results.items()
            }
            logger.info(
                f"Tool execution results summary: {tool_results_summary} (Session: {session_id})"
            )

        # 3. Generate final response based on DB results
        final_response_obj = await get_response_with_db_info_grounding(
            user_message=preprocessed_user_message,
            history=history,
            tool_results=tool_results,
        )
        # Log the reasoning for the final response
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Final response object (Session: {session_id}): {final_response_obj}"
            )
        logger.info(
            f"Final response reasoning (length: {len(final_response_obj.reasoning)}). (Session: {session_id})"
        )
        bot_reply = final_response_obj.response_to_user
        logger.info(
            f"Final response generated after tool use (length: {len(bot_reply)}). (Session: {session_id})"
        )

    # 4. Store the conversation turn in history
    try:
        # Use the add_chat_turn from app.memory.service
        await memory_service.add_chat_turn(
            session_id=session_id,
            user_message=preprocessed_user_message,
            bot_message=bot_reply,
            redis_client=redis_client,
        )
        logger.debug(f"Chat turn added to history (Session: {session_id})")
    except Exception as e:
        # Log the exception details, including stack trace
        logger.error(
            f"Failed to add chat turn to history for session {session_id}: {e}",
            exc_info=True,
        )
        # Still return the bot reply even if history saving fails

    return bot_reply, session_id
