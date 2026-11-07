FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for clean networking compiles
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first (Better Docker caching behavior)
COPY requirements.txt .

# Upgrade pip and install Python dependencies with an extended network timeout
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy application source code and views
COPY app/app.py .
COPY app/templates ./templates

EXPOSE 5000

CMD ["python", "/app/app.py"]
