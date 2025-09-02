# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

# System deps (if any audio libs are later required, add them here)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt /app/backend/requirements.txt
RUN pip install -r requirements.txt

# App source
COPY . /app/backend

# Copy placeholder data file next to server for convenience (fallback also exists)
COPY ../data/German_studies.text /app/backend/German_studies.text

# Cloud Run provides $PORT
ENV PORT=8080
EXPOSE 8080

# Start using uvicorn
CMD ["uvicorn", "server_radpair:app", "--host", "0.0.0.0", "--port", "${PORT}"]

