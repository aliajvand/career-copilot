# Production Dockerfile for Career Co-Pilot Pro
# Compatible with Hugging Face Spaces (Port 7860), Render, and Koyeb (Port 8000/8080)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Initialize clean database
RUN python -m core.db

# Expose standard Hugging Face Spaces / Render port
EXPOSE 7860

# Run unified cloud runner (starts Web Dashboard & Telegram Bot worker)
CMD ["python", "run_cloud.py"]
