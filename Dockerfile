FROM python:3.12.10-alpine as builder

# Set environment variables for build stage
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Add Poetry to PATH early so it's available in subsequent RUN commands
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install build dependencies and Poetry first
RUN apk update && \
    apk add --no-cache --virtual .build-deps \
        curl \
        build-base \
        python3-dev \
        libffi-dev \
        postgresql-dev && \
    curl -sSL https://install.python-poetry.org | python3 -

# Set the working directory
WORKDIR /app

# Copy only the dependency definition files first to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install production dependencies only using the copied files
RUN poetry install --no-dev --no-root && \
    apk del .build-deps && \
    rm -rf /var/cache/apk/*

# Copy the rest of the application code
COPY ./app ./app
COPY ./static ./static

# Stage 2: Create the final slim production image
FROM python:3.12.10-alpine as final

# Set environment variables for runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Create a non-root user and group for security
RUN addgroup -g 1001 -S appuser && \
    adduser -u 1001 -S appuser -G appuser -h /home/appuser -s /bin/bash

# Install runtime dependencies:
RUN apk update && \
    apk add --no-cache \
        curl \
        libpq && \
    rm -rf /var/cache/apk/*

# Set the working directory
WORKDIR /app

# Copy installed Python packages (site-packages) and executables from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code FROM THE BUILDER STAGE
COPY --from=builder /app /app

# Ensure the non-root user owns the application files
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the port the app runs on (using the ENV variable)
EXPOSE ${PORT}

# Add HEALTHCHECK instruction to verify the app is responsive
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Command to run the application using Gunicorn
CMD gunicorn -k uvicorn.workers.UvicornWorker -w 1 --bind "0.0.0.0:${PORT}" app.main:app