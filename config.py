import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ตั้งค่าการอัปโหลดไฟล์
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

    SESSION_TYPE = 'filesystem'  # 🗂 ใช้ไฟล์ระบบเก็บ session
    SESSION_PERMANENT = False  # ❌ Session หายไปเมื่อปิดเบราว์เซอร์
    SESSION_USE_SIGNER = True  # ✅ ป้องกัน session ถูกแก้ไข
    PERMANENT_SESSION_LIFETIME = 3600  # ⏳ อายุ session = 1 ชั่วโมง
    SESSION_COOKIE_SECURE = False  # ✅ ปิด secure cookie (ใช้ HTTP)
