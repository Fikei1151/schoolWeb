import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv()  # โหลดค่าจาก .env

class Config:
    SECRET_KEY = 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost/dbname')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AWS S3 Config
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET')
    AWS_S3_REGION = os.getenv('AWS_S3_REGION')
    
    # ใช้ S3 แทนโฟลเดอร์อัปโหลด
    UPLOAD_FOLDER = f"https://{AWS_S3_BUCKET}.s3.{AWS_S3_REGION}.amazonaws.com/uploads/"

    #ด่อนุญาตเฉพาะไฟล์ที่อนุญาต
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 3600
    SESSION_COOKIE_SECURE = False
