# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# tiny base + uv
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

WORKDIR /app
# For step 1, copy the project in (we’ll optimize later)
# Copy only requirements for cache efficiency
COPY config/requirements.txt /tmp/requirements.txt
RUN uv pip install --system -r /tmp/requirements.txt
COPY app /app

# Include Alembic config and migration scripts in the image
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

# Default Alembic config path (used by entrypoint and manual runs)
ENV ALEMBIC_CONFIG=/app/alembic.ini

# Entrypoint that waits for DB and runs migrations before launching the app
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Ensure our entrypoint runs on container start
ENTRYPOINT ["/entrypoint.sh"]

CMD ["uv", "run", "uvicorn", "main:app", "--host=0.0.0.0", "--port=8000", "--proxy-headers"]