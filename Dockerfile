FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /app/

# Expose ports: DNS (UDP/TCP), Admin/DoH (HTTP), DoT (TLS)
EXPOSE 53/udp 53/tcp 8080/tcp 853/tcp

# Run the application
CMD ["python", "main.py"]
