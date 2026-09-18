FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for CBC solver (PuLP)
RUN apt-get update && apt-get install -y --no-install-recommends \
    coinor-cbc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run the application
# Secrets must be injected via environment variables at runtime, NOT baked in
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
