import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.tools.tool_registry import TOOL_REGISTRY
from app.tools.formatters.tool_formatters import TOOL_FORMATTERS


logger = logging.getLogger(__name__)


async def execute_tools_sequentially(
    tool_calls: List, db: AsyncSession
) -> Dict[str, Any]:
    """
    Executes identified tools sequentially using the same DB session,
    wrapping all calls in a single transaction.
    """
    all_tool_results: Dict[str, Any] = {}
    logger.info(f"Executing {len(tool_calls)} tools sequentially...")
    async with db.begin():
        for tool_call in tool_calls:
            tool_name = tool_call.name
            # Extract parameters from the model fields, excluding 'name'
            tool_params = tool_call.model_dump(exclude={"name"})
            tool_func = TOOL_REGISTRY.get(tool_name)

            if not tool_func:
                logger.warning(f"Tool '{tool_name}' not found in registry.")
                all_tool_results[tool_name] = {
                    "error": f"Tool '{tool_name}' not available."
                }
                continue

            try:
                # Log tool name and parameter keys, not full values at INFO level
                logger.info(
                    f"Running tool: {tool_name} with parameter keys: {list(tool_params.keys())}"
                )
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Tool '{tool_name}' params: {tool_params}")

                raw_results = await tool_func(params=tool_params, db=db)

                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Raw results for tool '{tool_name}': {raw_results}")
                else:
                    # Log a summary of raw results, e.g., type and length if list/dict
                    if isinstance(raw_results, list):
                        logger.info(
                            f"Raw results for tool '{tool_name}': list of {len(raw_results)} items."
                        )
                    elif isinstance(raw_results, dict):
                        logger.info(
                            f"Raw results for tool '{tool_name}': dict with {len(raw_results)} keys."
                        )
                    else:
                        logger.info(
                            f"Raw results for tool '{tool_name}' received (type: {type(raw_results).__name__})."
                        )

                # Format the results if a formatter exists
                formatter = TOOL_FORMATTERS.get(tool_name)
                if formatter:
                    try:
                        # Special case for screenings formatter which needs halls_and_screening_times
                        if tool_name == "cinemas":
                            include_times = tool_params.get(
                                "halls_and_screening_times", False
                            )
                            formatted_results = formatter(
                                raw_results, halls_and_screening_times=include_times
                            )
                        else:
                            formatted_results = formatter(raw_results)

                        all_tool_results[tool_name] = formatted_results
                        logger.info(
                            f"Tool '{tool_name}' completed and results formatted."
                        )
                    except Exception as fmt_e:
                        logger.error(
                            f"Error formatting results for tool '{tool_name}': {fmt_e}",
                            exc_info=True,
                        )
                        # Store raw results or an error message upon formatting failure
                        all_tool_results[tool_name] = {
                            "error": f"Failed to format results for tool '{tool_name}'.",
                        }
                        if logger.isEnabledFor(logging.DEBUG) and raw_results:
                            logger.debug(
                                f"Raw results for tool '{tool_name}' (formatting failed): {raw_results}"
                            )
                else:
                    # No formatter defined for this tool, store raw results
                    # For history, raw results are currently expected (list of strings)
                    all_tool_results[tool_name] = raw_results
                    logger.info(f"Tool '{tool_name}' completed. No formatter applied.")

            except Exception as e:
                logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
                all_tool_results[tool_name] = {
                    "error": f"Failed to execute tool '{tool_name}'."
                }
                # Re-raise the exception to stop the sequence and trigger transaction rollback
                raise e

    logger.info("Sequential tool execution finished.")
    return all_tool_results
