FROM python:3.11-slim

# Install system dependencies for PyMuPDF, Tesseract, pdfplumber
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libmagic1 \
    poppler-utils \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
