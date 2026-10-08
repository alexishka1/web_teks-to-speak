FROM python:3.11-slim

# Install system dependencies (ffmpeg is essential for audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create models and storage directories
RUN mkdir -p /app/storage/audio /app/storage/models

COPY . .

# Unduh model ONNX resmi Piper bahasa Indonesia dengan verifikasi checksum MD5
RUN python scripts/download_voice.py

ENV PORT=8000
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
