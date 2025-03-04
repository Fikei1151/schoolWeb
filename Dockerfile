# ใช้ Python 3.9 slim เพื่อให้ image เบา
FROM python:3.11-slim

# กำหนด working directory
WORKDIR /app

# คัดลอกไฟล์ทั้งหมดไปยัง container
COPY . /app

# ติดตั้ง dependencies
RUN pip install --no-cache-dir -r requirements.txt

# รัน Gunicorn เมื่อ container เริ่ม
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "4"]