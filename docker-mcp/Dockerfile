FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI (for running docker commands inside container)
RUN apt-get update && apt-get install -y \
    docker.io \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port for HTTP transport (optional)
EXPOSE 8000

# Run MCP server
CMD ["python", "server.py"]
