# ============================================================
# Craft Project Dockerfile
# Django + Daphne + SQLite
# Multi-stage Docker build for smaller and cleaner image
# ============================================================


# ============================================================
# 1) Base Stage
# ------------------------------------------------------------
# This stage contains the common runtime environment.
# It is used by both builder and final stages.
# ============================================================

FROM python:3.11-slim-bookworm AS base

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Force Python logs to appear immediately
ENV PYTHONUNBUFFERED=1

# Set application working directory
WORKDIR /app

# Install runtime system dependencies only.
# Also upgrade pip/wheel/jaraco.context to reduce Docker Scout warnings.
RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/* && \
    python -m pip install --no-cache-dir --upgrade \
    pip \
    setuptools \
    wheel==0.47.0 \
    jaraco.context==6.1.2


# ============================================================
# 2) Builder Stage
# ------------------------------------------------------------
# This stage installs Python dependencies inside a virtual env.
# The final image will copy only the ready .venv from here.
# ============================================================

FROM base AS builder

# Install build dependencies.
# These are needed only while installing Python packages with C extensions.
# They will NOT be copied to the final image.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment inside /app
RUN python -m venv /app/.venv

# Make the virtual environment active for the next commands
ENV PATH="/app/.venv/bin:$PATH"

# Copy requirements first to use Docker layer caching.
# If source code changes but requirements.txt does not,
# Docker can reuse the dependency installation layer.
COPY requirements.txt ./

# Install Python dependencies inside .venv
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt


# ============================================================
# 3) Final Stage
# ------------------------------------------------------------
# This is the production/runtime image.
# It contains:
# - runtime OS dependencies
# - Python virtual environment
# - application source code
# - existing SQLite database with correct permissions
# ============================================================

FROM base AS final

# Create a non-root user for better security
RUN useradd --system --create-home --shell /bin/bash appuser

# Copy the virtual environment from the builder stage.
# Important:
# This does NOT copy .venv from your local machine.
# It copies the .venv created inside the builder stage.
COPY --chown=appuser:0 --from=builder /app/.venv ./.venv

# Copy application source code.
# This should include db.sqlite3 if you want to ship your existing SQLite file.
COPY --chown=appuser:0 . .

# Fix permissions for the EXISTING SQLite database.
# We use test -f to make the build fail clearly if db.sqlite3 is missing.
#
# SQLite needs write permission on:
# 1) The database file itself: /app/db.sqlite3
# 2) The parent directory: /app
#
# Because SQLite may create temporary files like:
# db.sqlite3-journal
# db.sqlite3-wal
# db.sqlite3-shm
RUN if [ -f /app/db.sqlite3 ]; then \
        chown appuser:0 /app/db.sqlite3 && \
        chmod 664 /app/db.sqlite3; \
    fi && \
    chown appuser:0 /app && \
    chmod 775 /app

# Switch to non-root user
USER appuser

# Use the virtual environment by default
ENV PATH="/app/.venv/bin:$PATH"

# Expose Django/Daphne port
EXPOSE 8000

# Start the ASGI application using Daphne
CMD ["opentelemetry-instrument", "daphne", "-b", "0.0.0.0", "-p", "8000", "Handcrafts.asgi:application"]