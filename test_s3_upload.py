import os
from flask import Flask
from werkzeug.datastructures import FileStorage
from utils.s3_utils import upload_file_to_s3
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

def test_s3_upload():
    """ทดสอบการอัปโหลดไฟล์ไปยัง S3"""
    # ตรวจสอบว่ามีไฟล์ตัวอย่างหรือไม่
    test_image_path = 'static/profile_pics/default_profile.png'
    if not os.path.exists(test_image_path):
        print(f"ไม่พบไฟล์ตัวอย่าง: {test_image_path}")
        return False
    
    # อ่านข้อมูลไฟล์ทั้งหมดก่อน
    with open(test_image_path, 'rb') as f:
        file_data = f.read()
    
    # สร้าง FileStorage object จากข้อมูลที่อ่านมา
    from io import BytesIO
    file = FileStorage(
        stream=BytesIO(file_data),
        filename='test_upload.png',
        content_type='image/png'
    )
    
    # ทดสอบอัปโหลดไป S3
    print("กำลังทดสอบอัปโหลดไฟล์ไปยัง S3...")
    s3_url = upload_file_to_s3(file, "test", "test_upload.png")
    
    if s3_url:
        print(f"อัปโหลดสำเร็จ! URL: {s3_url}")
        return True
    else:
        print("อัปโหลดล้มเหลว")
        return False

if __name__ == "__main__":
    test_s3_upload()
