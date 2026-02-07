FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies (if needed for certain Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY docs/ ./docs/

# Create directory for generated PDFs
RUN mkdir -p /app/generated_pdfs

# Set default port (Cloud Run uses 8080)
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application (no --reload in production for faster startup)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
