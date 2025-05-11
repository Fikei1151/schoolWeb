import os
from config import Config
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

# ตรวจสอบและสร้างโฟลเดอร์ถ้าไม่มี
def ensure_folder_exists(folder_path):
    """Create folder if it doesn't exist"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)

# สร้างชื่อไฟล์ที่ไม่ซ้ำกัน
def generate_unique_filename(original_filename):
    """Generate unique filename using timestamp and UUID"""
    filename, extension = os.path.splitext(original_filename)
    unique_name = f"{filename}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:8]}{extension}"
    return secure_filename(unique_name)

def init_storage():
    """Initialize local storage folders"""
    folders = ['uploads', 'profile_pics', 'temp']
    for folder in folders:
        folder_path = os.path.join(Config.UPLOAD_FOLDER, folder)
        ensure_folder_exists(folder_path)
    return True

# ฟังก์ชันอัปโหลดไฟล์ไปยังโฟลเดอร์ท้องถิ่น แทน S3
def upload_file_to_storage(file, folder="uploads", filename=None):
    """Save file to local storage and return URL path"""
    if not file:
        return None
        
    if filename is None:
        filename = generate_unique_filename(file.filename)
    else:
        filename = secure_filename(filename)
    
    target_folder = os.path.join(Config.UPLOAD_FOLDER, folder)
    ensure_folder_exists(target_folder)
    file_path = os.path.join(target_folder, filename)
    
    try:
        current_position = file.tell()
        file.seek(0)
        file.save(file_path)
        file.seek(current_position)
        
        return f"{Config.UPLOADS_URL_PATH}{folder}/{filename}"
    except Exception as e:
        print(f"Error saving file: {e}")
        return None

def get_file_url(object_name):
    """Get URL path for file download from local storage"""
    if '/' in object_name:
        folder, filename = object_name.split('/', 1)
        return f"{Config.UPLOADS_URL_PATH}{folder}/{filename}"
    return f"{Config.UPLOADS_URL_PATH}uploads/{object_name}"

def delete_file(object_name):
    """Delete file from local storage"""
    try:
        if '/' in object_name:
            folder, filename = object_name.split('/', 1)
        else:
            folder, filename = 'uploads', object_name
            
        file_path = os.path.join(Config.UPLOAD_FOLDER, folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"Error deleting file: {e}")
    return False

# ฟังก์ชันอัปโหลดไฟล์ไปยัง S3 (ใช้ local storage แทนเนื่องจากยังไม่มีการตั้งค่า S3)
def upload_file_to_s3(file, folder="uploads", filename=None):
    """
    อัปโหลดไฟล์ไปยัง S3 (แต่ตอนนี้ใช้ local storage แทนเนื่องจากยังไม่มีการตั้งค่า S3)
    """
    # เรียกใช้ฟังก์ชัน upload_file_to_storage แทน
    return upload_file_to_storage(file, folder, filename)

# Initialize storage
storage = init_storage()
