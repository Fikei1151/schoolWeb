# Use Python 3.9 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload directories
RUN mkdir -p /app/uploads /app/profile_pics /app/temp

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# ลดการใช้ CPU โดยปรับจำนวน workers และเพิ่ม timeout
# ใช้ 2 workers (ลดจาก 4) และเพิ่ม timeout เป็น 120 วินาที
# เพิ่ม max-requests เพื่อป้องกัน memory leak
CMD ["gunicorn", "--workers=1", "--threads=4", "--worker-class=gthread", "--timeout=120", "--max-requests=1000", "--max-requests-jitter=50", "--bind=0.0.0.0:8000", "app:app"]