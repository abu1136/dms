FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and comprehensive fonts for Unicode support
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    fonts-dejavu-core \
    fonts-dejavu \
    fonts-liberation \
    fonts-liberation2 \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-mono \
    fonts-noto-color-emoji \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directory
RUN mkdir -p /app/storage/uploads

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
