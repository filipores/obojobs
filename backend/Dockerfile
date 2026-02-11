FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
      gcc \
      curl \
      tesseract-ocr \
      tesseract-ocr-deu \
      poppler-utils \
      && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn for production
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

# Create upload and database directories
RUN mkdir -p uploads db

# Make entrypoint script executable (already copied by COPY . .)
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 5002

# Run migrations then start gunicorn
ENTRYPOINT ["/app/entrypoint.sh"]
