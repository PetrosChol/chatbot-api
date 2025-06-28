import instructor
import google.generativeai as genai
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure the Google Generative AI client with the API key from settings.
if settings.GEMINI_API_KEY:
    # Use .get_secret_value() for Pydantic SecretStr to safely retrieve the key.
    genai.configure(api_key=settings.GEMINI_API_KEY.get_secret_value())
    logger.info("Google Generative AI client configured.")
else:
    logger.error(
        "GEMINI_API_KEY not found in settings. Google Generative AI client not configured. "
        "Please set the GEMINI_API_KEY in your environment."
    )

model_name: str = settings.MODEL_NAME # The Gemini model to use (e.g., 'gemini-pro').

client = None # Global variable to hold the Instructor-enhanced Gemini client.

# Initialize the Instructor client for the specified Gemini model.
try:
    # First, create the base Google Generative Model.
    gemini_base_client = genai.GenerativeModel(model_name=model_name)

    # Then, wrap it with 'instructor' for structured output capabilities.
    # use_async=True is crucial for non-blocking I/O in async applications.
    client = instructor.from_gemini(
        client=gemini_base_client,
        use_async=True,
    )
    logger.info(f"Instructor client created for model: '{model_name}'.")
except Exception as e:
    logger.error(f"Failed to create Instructor client for model '{model_name}': {e}", exc_info=True)
    client = None # Ensure client is None if initialization fails.

def get_instructor_client():
    """
    Retrieves the pre-initialized Instructor-enhanced Google Gemini client.

    This function provides a centralized access point to the configured AI client,
    ensuring consistent usage across the application.

    Returns:
        The configured Instructor client instance.

    Raises:
        RuntimeError: If the Instructor client failed to initialize during
                      application startup (e.g., missing API key, network issues,
                      or invalid model name).
    """
    if client is None:
        # Prevent downstream components from trying to use an uninitialized client.
        raise RuntimeError(
            "Instructor client is not initialized. Check API key, network, and model configuration."
        )
    return client