import boto3
from config import Config
import os

# ตั้งค่า S3 Client
def create_s3_client(config):
    """สร้าง S3 client จากการตั้งค่า"""
    if config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY:
        return boto3.client(
            "s3",
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_S3_REGION
        )
    return None

# ฟังก์ชันอัปโหลดไฟล์ไปยัง S3
def upload_file_to_s3(file, folder="uploads", filename=None):
    """อัปโหลดไฟล์ไปยัง S3 และคืนค่า URL"""
    if not s3_client:
        return None
        
    if filename is None:
        filename = file.filename
        
    object_name = f"{folder}/{filename}"
    
    # อ่านข้อมูลไฟล์ทั้งหมดก่อนอัปโหลด
    try:
        # บันทึกตำแหน่งปัจจุบัน
        current_position = file.tell()
        # กลับไปที่ต้นไฟล์
        file.seek(0)
        
        # อัปโหลดไฟล์โดยใช้ upload_fileobj ซึ่งเร็วกว่า put_object
        try:
            s3_client.upload_fileobj(
                file,
                Config.AWS_S3_BUCKET,
                object_name,
                ExtraArgs={
                    'ACL': 'public-read',  # ตั้งค่าให้ไฟล์เป็นสาธารณะ
                    'ContentType': file.content_type  # ตั้งค่า Content-Type ให้ถูกต้อง
                }
            )
            
            # กลับไปที่ตำแหน่งเดิม
            file.seek(current_position)
            
            return f"https://{Config.AWS_S3_BUCKET}.s3.{Config.AWS_S3_REGION}.amazonaws.com/{object_name}"
        except Exception as e:
            print(f"Error uploading to S3: {e}")
            # กลับไปที่ตำแหน่งเดิม
            file.seek(current_position)
            return None
            
    except ValueError as e:
        # ถ้าไฟล์ถูกปิดไปแล้ว
        print(f"File error: {e}")
        return None

# ฟังก์ชันสร้าง presigned URL สำหรับการดาวน์โหลดไฟล์จาก S3
def get_presigned_url(object_name, expiration=3600):
    """สร้าง presigned URL สำหรับการดาวน์โหลดไฟล์จาก S3"""
    if not s3_client:
        return None
        
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': Config.AWS_S3_BUCKET,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
        return response
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None

# สร้าง S3 client
s3_client = create_s3_client(Config)
