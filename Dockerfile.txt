# ใช้ Python 3.11 slim เป็น base image
FROM python:3.11-slim AS build-stage

# ตั้ง working directory
WORKDIR /app

# คัดลอกไฟล์ทั้งหมดไปยัง container
COPY . /app

# ติดตั้ง pip และ dependencies
RUN apt-get update && apt-get install -y python3-pip && \
    pip install --no-cache-dir -r requirements.txt

# รัน Gunicorn เมื่อ container เริ่ม
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "4"]