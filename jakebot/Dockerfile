# Use Python 3.10 as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for logs
RUN mkdir -p /app/logs

# Set Python path to include app directory
ENV PYTHONPATH=/app

# Expose port for FastAPI
EXPOSE 5000

# Command to run the application with proper module path
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5000"] 