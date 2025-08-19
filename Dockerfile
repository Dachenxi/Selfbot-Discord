#############################
# Multi-stage (builder -> runtime) optional; here single slim image is enough
# Base image with Python 3.13 (adjust if not yet available; use 3.12 if 3.13 missing)
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1 \
	PYTHONDONTWRITEBYTECODE=1

# Install system deps (git needed for VCS requirement) then clean
RUN apt-get update \
	&& apt-get install -y --no-install-recommends git \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency file first for layer caching
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create database & log directories with proper permissions
RUN mkdir -p database log \
	&& useradd -m -u 1000 appuser \
	&& chown -R appuser:appuser /app \
	&& chmod -R 755 /app/database \
	&& chmod -R 755 /app/log

USER appuser

# Expose nothing (Discord selfbot does outbound only) – kept for clarity
# EXPOSE 8000

CMD ["python", "main.py"]
