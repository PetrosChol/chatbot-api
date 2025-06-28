Okay, based on our detailed discussions and the plan we've built, here is a summary of your application:

**Application Name:** "Alex" Chatbot

**Core Purpose:**
To serve as an intelligent, conversational information assistant for the website ThessalonikiGuide.gr. It aims to understand user queries (likely in Greek or English) about Thessaloniki and provide relevant, up-to-date information by leveraging both AI and structured data sources.

**High-Level Functionality:**

1.  **Conversational Interface:** Users interact with Alex via a chat interface, sending messages to a central API endpoint (`/api/v1/chat`).
2.  **LLM Brain:** At its core, the application uses Google's Gemini language model, integrated via the `instructor` library. This allows Alex to understand natural language, parse user intent, and decide on the best course of action (answer directly, ask for clarification, or use a tool).
3.  **Tool-Using Agent:** A key feature is Alex's ability to function as an agent. Based on the user's query, the LLM can determine that specific, structured information is required and identify the appropriate internal "tool" to call.
4.  **Information Retrieval:** Dedicated tools query a PostgreSQL database (using async SQLAlchemy and SQLModel) to fetch specific information like:
    *   Power and Water Outages (using fuzzy/regex matching)
    *   Musical and Theatrical Performances (using fuzzy matching)
    *   Movie Screenings (using fuzzy matching)
    *   Hospital Shifts (using regex matching)
    *   Thessaloniki History (using OpenAI embeddings and `pgvector` for semantic search).
5.  **Response Synthesis:** After retrieving data from tools (if any), the LLM synthesizes this information, along with the conversation history, into a coherent, natural language response for the user, aiming to match the user's original language.

**Key Technical Aspects:**

*   **Backend Framework:** FastAPI (Asynchronous Python web framework).
*   **Database:** PostgreSQL with the `pgvector` extension (for history search). Accessed via SQLAlchemy (async) and SQLModel.
*   **Caching/Session Store:** Redis (async) used primarily to store conversation history for session management.
*   **Session Management:** HTTP cookies (`chat_session_id`) link users to their conversation history stored in Redis.
*   **LLM Integration:** `google-generativeai` library for Gemini, `instructor` for structured output (tool selection), `openai` library for embeddings.
*   **Query Building:** Uses a pattern of dedicated "statement builder" functions for each tool to create SQLAlchemy queries based on parameters, separating query logic from execution. Tool execution is planned to be sequential initially for simplicity and session safety.
*   **Rate Limiting:** Implemented using `fastapi-limiter` to protect the chat endpoint.
*   **Security:** Includes essential security headers (HSTS, X-Content-Type-Options, X-Frame-Options) added via middleware.
*   **Development:** Uses Poetry for dependency management, VS Code as the IDE, Git (`develop`/`main` branches) for version control, and includes unit/integration tests (`pytest`).
*   **Deployment:** Containerized using Docker and designed for deployment on DigitalOcean App Platform, utilizing DO Managed Databases for PostgreSQL and Redis.

In essence, "Alex" is designed to be a smart, data-aware chatbot that goes beyond simple LLM responses by grounding its answers in specific, queryable data relevant to Thessaloniki, all served via a modern, scalable FastAPI backend.